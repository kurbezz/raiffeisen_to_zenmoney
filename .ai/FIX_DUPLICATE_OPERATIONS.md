# Fix for Duplicate Transfer Operations (97715RSD Issue)

## Problem Description

On February 1st, two operations with amount 97715 RSD were created in ZenMoney instead of one single transfer operation. This happened because:

1. The bank email statements contained two linked operations:
   - One debit operation: -97715 RSD (outgoing)
   - One credit operation: +97715 RSD (incoming)

2. These operations shared a common reference (97715RSD) linking them together.

3. However, the original code only linked operations if they had **different currencies** (for currency exchanges), so same-currency linked operations were treated as two separate transactions and both were imported.

## Root Cause

In `src/services/operations/preparer.py`, the linking logic had this condition:

```python
if _are_operations_linked(op1, op2):
    if (
        op1.currency != op2.currency  # ← Only links different currencies!
        and (
            (op1.amount < 0 and op2.amount > 0)
            or (op1.amount > 0 and op2.amount < 0)
        )
        and (_is_currency_exchange(op1) or _is_currency_exchange(op2))
    ):
        # Create TransitionOperation
```

This prevented linking of same-currency operations, even if they were clearly a debit/credit pair representing a single transfer.

## Solution

Modified the `prepare_operations()` function in `src/services/operations/preparer.py` to:

1. **Initialize `processed_operations` set** - Track which operations have already been combined
2. **Add same-currency linking logic** - Before processing currency exchanges, check for same-currency operation pairs:
   - Both operations must be linked (same reference)
   - Same currency (both RSD)
   - Same absolute amount but opposite signs (one positive, one negative)
   - Opposite sign check: ensures they're a debit/credit pair
3. **Combine paired operations** - When found, mark both as processed and add only the positive (incoming) operation as a `SimpleOperation`
4. **Preserve currency exchange logic** - The original currency exchange detection remains for multi-currency transactions

## Code Changes

### Before

```python
for raw_operation, account_number in all_raw_operations:
    if id(raw_operation) not in processed_operations:  # processed_operations was undefined!
        # ... create operation
```

### After

```python
processed_operations = set()

# Link same-currency transfer operations
for i, (op1, acc1) in enumerate(all_raw_operations):
    if id(op1) in processed_operations:
        continue
    
    for j, (op2, acc2) in enumerate(all_raw_operations[i + 1 :], i + 1):
        if id(op2) in processed_operations:
            continue
        
        # Check if operations are linked and have opposite amounts and same currency
        if _are_operations_linked(op1, op2):
            if (
                op1.currency == op2.currency
                and abs(op1.amount) == abs(op2.amount)
                and (
                    (op1.amount < 0 and op2.amount > 0)
                    or (op1.amount > 0 and op2.amount < 0)
                )
            ):
                # Mark both as processed, add only income operation
                processed_operations.add(id(op1))
                processed_operations.add(id(op2))
                
                income_op = op2 if op2.amount > 0 else op1
                simple_op = SimpleOperation.from_raw(income_op)
                operations.append(simple_op)
                break
            # ... (currency exchange logic unchanged)

# Process remaining operations
for raw_operation, account_number in all_raw_operations:
    if id(raw_operation) not in processed_operations:
        # ... create operation
```

## Impact

- **Before**: Two operations with reference 97715RSD on 2024-02-01 → Created 2 transactions in ZenMoney
- **After**: Two operations with reference 97715RSD on 2024-02-01 → Creates 1 transaction in ZenMoney (the positive/income one)

## How It Works

For example, with operations from the bank statement:
1. Operation A: Date=2024-02-01, Amount=-97715, Currency=RSD, Reference=97715RSD
2. Operation B: Date=2024-02-01, Amount=+97715, Currency=RSD, Reference=97715RSD

The fix:
1. Detects they're linked (same reference)
2. Sees they're same currency with matching absolute amounts
3. Checks they have opposite signs (A is negative, B is positive)
4. Marks both as processed
5. Creates a single `SimpleOperation` from operation B (the positive/income one)
6. Only one transaction is sent to ZenMoney

## Testing

To verify the fix works:
1. Run the main script with transactions that have linked debit/credit pairs
2. Verify that only ONE transaction is created in ZenMoney (not two)
3. Check that the transaction shows the correct amount and date
4. Verify currency exchanges still work correctly (for different currency pairs)

## Files Modified

- `src/services/operations/preparer.py` - Added same-currency transfer linking logic