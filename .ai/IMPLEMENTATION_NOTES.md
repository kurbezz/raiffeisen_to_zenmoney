# Implementation Notes - Duplicate Operations Fix

## Summary of Changes

Fixed an issue where same-currency linked operations (debit/credit pairs) were being imported as two separate transactions instead of one.

**File Modified:** `src/services/operations/preparer.py`

## The Bug

In the original code, the `processed_operations` variable was referenced but never initialized:

```python
for raw_operation, account_number in all_raw_operations:
    if id(raw_operation) not in processed_operations:  # NameError: processed_operations not defined!
```

Additionally, the operation linking logic only handled currency exchanges (different currencies) and ignored same-currency transfer pairs.

## The Fix

### 1. Initialize `processed_operations`
```python
processed_operations = set()
```

### 2. Add Same-Currency Linking Logic
Added a loop that runs before regular operation processing to detect and combine:
- Operations linked by reference (matching `_are_operations_linked()`)
- Same currency on both operations
- Matching absolute amounts
- Opposite signs (one debit, one credit)

When detected, only the positive/income operation is added to the operations list.

### 3. Preserve Existing Logic
The currency exchange detection logic remains unchanged and runs after the same-currency linking.

## Edge Cases Handled

### Edge Case 1: Multiple Linked Operations
**Scenario:** Operation A links to B, B links to C
**How it's handled:** The nested loop processes pairs sequentially. Once A-B are matched and marked as processed, B won't be considered again when processing subsequent pairs.

### Edge Case 2: Zero-Amount Operations
**Scenario:** Operation has 0 amount
**How it's handled:** The statement parsing skips zero amounts:
```python
if operation.attrib.get("Duguje", "0") != "0" or operation.attrib.get("Potrazuje", "0") != "0":
```

### Edge Case 3: Negative Amounts Consistency
**Scenario:** Debit operations have negative amounts, credit operations have positive amounts
**How it's handled:** The code checks for opposite signs explicitly:
```python
(op1.amount < 0 and op2.amount > 0) or (op1.amount > 0 and op2.amount < 0)
```

### Edge Case 4: Rounding/Precision Issues
**Scenario:** Linked operations have amounts like -97715.00 and +97715.01
**Potential Problem:** `abs(op1.amount) == abs(op2.amount)` uses exact equality
**Current Status:** This would NOT match. Future enhancement: Consider using `math.isclose()` for floating-point comparison

```python
import math
# Better:
math.isclose(abs(op1.amount), abs(op2.amount), rel_tol=1e-9)
```

### Edge Case 5: Reference Field Being Empty
**Scenario:** Operations have no reference field
**How it's handled:** `_are_operations_linked()` checks for None/empty references:
```python
if op1.reference and op2.reference and op1.reference == op2.reference:
    return True  # Only returns True if both have references
```

### Edge Case 6: Deel Transfers and Cash Withdrawals
**Scenario:** A Deel transfer operation matches the linking criteria
**How it's handled:** Deel and cash withdrawal detection happens AFTER the linking phase, so linked operations are handled first, preventing misclassification.

## Algorithm Complexity

### Time Complexity
- Deduplication: O(n) where n = number of raw operations
- Linking phase: O(n²) worst case, but typically much less due to early breaks
- Processing unlinked: O(n)
- **Total: O(n²)** - acceptable for typical email statement volumes (50-200 operations)

### Space Complexity
- `seen_operations`: O(n)
- `processed_operations`: O(n)
- **Total: O(n)**

## Integration Points

### Affected Functions
- `prepare_operations()` - Main entry point, contains the fix
- `_are_operations_linked()` - Used to detect linked pairs
- `_is_currency_exchange()` - Used for currency exchange detection
- `_is_deel_transfer()` - Not affected
- `_is_cash_withdrawal()` - Not affected

### Downstream Impact
- `filter.py` - Filters the resulting operations (no changes needed)
- `zen_money/preparer.py` - Creates ZenMoney transactions (no changes needed)

## Testing Recommendations

### Unit Test Cases

1. **Same-Currency Transfer Pair**
   ```
   Input: Op1(-100 RSD, Ref='100'), Op2(+100 RSD, Ref='100')
   Expected: 1 SimpleOperation with amount +100
   ```

2. **Currency Exchange**
   ```
   Input: Op1(-100 USD, Ref='FX1'), Op2(+12000 RSD, Ref='FX1')
   Expected: 1 TransitionOperation
   ```

3. **Different Amounts, Same Currency**
   ```
   Input: Op1(-100 RSD, Ref='100'), Op2(+200 RSD, Ref='100')
   Expected: 2 SimpleOperations (not linked)
   ```

4. **Unlinked Operations**
   ```
   Input: Op1(-100 RSD, Ref='001'), Op2(+100 RSD, Ref='002')
   Expected: 2 SimpleOperations (different references)
   ```

5. **Multiple Pairs**
   ```
   Input: 4 ops forming 2 pairs
   Expected: 2 SimpleOperations (1 from each pair)
   ```

### Integration Test
1. Run with real email statements containing same-currency transfer pairs
2. Verify ZenMoney receives only 1 transaction per pair
3. Verify currency exchanges still work correctly
4. Check no operations are lost or duplicated

## Performance Considerations

The O(n²) linking loop is efficient enough for typical use cases:
- 50 operations: ~2,500 comparisons
- 100 operations: ~10,000 comparisons
- 200 operations: ~40,000 comparisons

All negligible on modern hardware. However, if email volume increases significantly:
1. Could optimize with a reference-based index:
```python
refs_to_operations = {}
for op in all_raw_operations:
    if op.reference:
        if op.reference not in refs_to_operations:
            refs_to_operations[op.reference] = []
        refs_to_operations[op.reference].append(op)

# Then only compare operations with same reference
for ref, ops in refs_to_operations.items():
    if len(ops) == 2:
        # Link if they match other criteria
```

2. Or use a hash-based approach for description matching.

## Future Enhancements

1. **Floating-Point Precision**
   - Use `math.isclose()` instead of exact equality for amounts
   
2. **Performance Optimization**
   - Index operations by reference for O(n log n) linking
   
3. **Configuration**
   - Make "matching absolute amounts" rule configurable
   - Add tolerance threshold for amount matching
   
4. **Logging**
   - Add debug-level logging for which operations are linked
   - Report linking statistics in summary
   
5. **Validation**
   - Add assertions to verify processed operations aren't added twice
   - Log warnings if multiple linking matches found for same operation

## Debugging Guide

### If Operations Still Get Duplicated

1. **Check deduplication output** - Are duplicates being caught at the raw stage?
   - Look for "ДУБЛИКАТ:" messages

2. **Add debug logging** - Insert this to see what's happening:
   ```python
   print(f"Checking linking: Op1={op1.amount} {op1.currency} (Ref={op1.reference})")
   print(f"                Op2={op2.amount} {op2.currency} (Ref={op2.reference})")
   ```

3. **Verify `_are_operations_linked()`** - Is it detecting links?
   - Check if references are populated in email parse
   - Look at description field - does it contain reference?

4. **Check amount matching** - Do they have exact same absolute value?
   - Print `abs(op1.amount)` vs `abs(op2.amount)`
   - Consider floating-point comparison issues

5. **Verify filter logic** - Is the filter catching duplicates?
   - Check `filter.py` key generation
   - Verify ZenMoney state is being loaded correctly

### If Valid Pairs Are Being Combined Incorrectly

1. **Verify opposite signs** - Check that operations have correct signs
2. **Verify references** - Are unrelated operations somehow sharing references?
3. **Check currency matching** - Are different currencies being treated as same?

## Version History

- **v1.0** (Current) - Initial implementation with same-currency transfer linking
  - Added `processed_operations` set initialization
  - Added same-currency pair detection logic
  - Preserved currency exchange detection