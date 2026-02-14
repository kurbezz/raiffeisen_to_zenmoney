# Duplicate Operations Fix - Visual Explanation

## Data Flow Before Fix

```
Email Statement (Feb 1, 2024)
├─ Operation A: -97715 RSD (Reference: 97715RSD)
└─ Operation B: +97715 RSD (Reference: 97715RSD)
         ↓
   Deduplication
   (Keys don't match because amounts differ)
         ↓
   [Debit Op A] [Credit Op B]
         ↓
   Operation Linking Check
   (FAILED: Currency is same, so skipped!)
         ↓
   [SimpleOp A] [SimpleOp B]
         ↓
   Filtering
   (Both pass - not duplicates in ZenMoney yet)
         ↓
   ZenMoney API
         ↓
   ❌ TWO TRANSACTIONS CREATED ❌
       Transaction 1: -97715 RSD
       Transaction 2: +97715 RSD
```

## Data Flow After Fix

```
Email Statement (Feb 1, 2024)
├─ Operation A: -97715 RSD (Reference: 97715RSD)
└─ Operation B: +97715 RSD (Reference: 97715RSD)
         ↓
   Deduplication
   (Keys don't match because amounts differ)
         ↓
   [Debit Op A] [Credit Op B]
         ↓
   NEW: Same-Currency Transfer Linking
   ├─ Check: Are they linked? YES (same reference)
   ├─ Check: Same currency? YES (both RSD)
   ├─ Check: Opposite amounts? YES (-97715 vs +97715)
   └─ Check: Opposite signs? YES (negative and positive)
         ↓
   Mark both as processed
   Add only positive operation (Op B)
         ↓
   [SimpleOp B only]
         ↓
   Filtering
   (Passes - not duplicate in ZenMoney)
         ↓
   ZenMoney API
         ↓
   ✅ ONE TRANSACTION CREATED ✅
       Transaction: +97715 RSD
```

## Operation Linking Logic

### Before (Only Currency Exchanges)
```
if _are_operations_linked(op1, op2):
    if (
        op1.currency != op2.currency        # ← PROBLEM: Skips same-currency!
        and opposite_amounts
        and is_currency_exchange
    ):
        # Link operations
```

### After (Same-Currency + Currency Exchanges)
```
if _are_operations_linked(op1, op2):
    # Case 1: Same-currency transfer (NEW!)
    if (
        op1.currency == op2.currency        # ← NEW: Handles same-currency
        and abs(op1.amount) == abs(op2.amount)
        and opposite_amounts
    ):
        # Link and combine operations
    
    # Case 2: Currency exchange (UNCHANGED)
    elif (
        op1.currency != op2.currency
        and opposite_amounts
        and is_currency_exchange
    ):
        # Link operations
```

## Example Scenarios

### Scenario 1: Same-Currency Transfer (NOW FIXED ✅)
```
Input Operations:
  Op1: 2024-02-01, -97715 RSD, Ref=97715RSD, Customer=Transfer Out
  Op2: 2024-02-01, +97715 RSD, Ref=97715RSD, Customer=Transfer In

Detection:
  ✓ Linked (same reference)
  ✓ Same currency (RSD)
  ✓ Matching amounts (abs value 97715)
  ✓ Opposite signs (-/+)

Result: 1 SimpleOperation created from Op2
```

### Scenario 2: Currency Exchange (UNCHANGED ✓)
```
Input Operations:
  Op1: 2024-02-01, -100 USD, Ref=FX001, Keywords=po kursu
  Op2: 2024-02-01, +12000 RSD, Ref=FX001, Keywords=po kursu

Detection:
  ✓ Linked (same reference)
  ✓ Different currencies (USD/RSD)
  ✓ Opposite signs (-/+)
  ✓ Is currency exchange

Result: 1 TransitionOperation created
```

### Scenario 3: Regular Operations (UNCHANGED ✓)
```
Input Operations:
  Op1: 2024-02-01, -500 RSD, Ref=001, Customer=Starbucks
  Op2: 2024-02-01, +1000 RSD, Ref=002, Customer=Salary

Detection:
  ✗ Not linked (different references)

Result: 2 SimpleOperations created (separate transactions)
```

## Key Differences

| Aspect | Before | After |
|--------|--------|-------|
| Same-currency debit/credit pairs | ❌ Creates 2 transactions | ✅ Creates 1 transaction |
| Currency exchanges | ✓ Works | ✓ Still works |
| Regular operations | ✓ Works | ✓ Still works |
| `processed_operations` variable | ❌ Undefined (bug) | ✅ Properly initialized |
| Code logic | Incomplete | Complete |

## Real-World Impact

### Before Fix
- Operations 1 and 2 on Feb 1 both imported
- User sees duplicate entries in ZenMoney
- Manual cleanup required
- Confusing account balance history

### After Fix
- Only operation 2 imported
- Single, clean transaction in ZenMoney
- Automatic duplicate prevention
- Accurate account records

## Testing Checklist

- [ ] Test with same-currency transfer pairs (like 97715RSD)
- [ ] Verify currency exchanges still work (USD↔RSD)
- [ ] Check regular operations aren't affected
- [ ] Confirm no new errors in deduplication
- [ ] Verify ZenMoney imports only 1 transaction per pair
- [ ] Test with Deel transfers (shouldn't be affected)
- [ ] Test with cash withdrawals (shouldn't be affected)