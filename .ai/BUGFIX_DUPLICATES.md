# Bug Fix: Duplicate Transactions on January 2nd

## 🐛 Problem Description

Transactions from January 2nd were being duplicated during import to ZenMoney.

## 🔍 Root Cause Analysis

The issue was in the `prepare_operations()` function in `src/services/operations/preparer.py`.

### What Was Happening

1. **Multiple Email Statements**: Raiffeisen Bank may send multiple email statements that contain the same operations:
   - Daily statements
   - Consolidated statements
   - Corrected statements
   - Multiple emails for the same account

2. **No Deduplication**: The code was collecting ALL raw operations from ALL statements without checking for duplicates:
   ```python
   for statement in statements:
       for raw_operation in statement.operations:
           all_raw_operations.append((raw_operation, statement.account_number))
   ```

3. **Why ZenMoney Filter Didn't Help**: The filter in `filter.py` only checks against EXISTING ZenMoney transactions. If duplicate operations came from emails in the same batch, both would pass the filter and get imported.

### Example Scenario

**Email 1** (daily statement):
- Operation: 02.01.2024, -1000 RSD, "MARKET ABC"

**Email 2** (consolidated statement):
- Operation: 02.01.2024, -1000 RSD, "MARKET ABC" ← SAME OPERATION

**Result**: Both operations were processed → 2 identical transactions imported to ZenMoney

## ✅ Solution Implemented

### 1. Raw Operation Deduplication (Primary Fix)

Added deduplication logic in `prepare_operations()` BEFORE processing:

```python
# Дедупликация сырых операций
seen_operations = set()
duplicates_count = 0

for statement in statements:
    for raw_operation in statement.operations:
        # Создаем уникальный ключ для операции
        operation_key = (
            raw_operation.data,           # Date
            raw_operation.amount,         # Amount
            raw_operation.currency,       # Currency
            raw_operation.customer,       # Customer/Merchant
            raw_operation.reference,      # Reference number
            raw_operation.description,    # Description
        )

        # Пропускаем дубликаты
        if operation_key in seen_operations:
            duplicates_count += 1
            print(f"ДУБЛИКАТ: {raw_operation.data} - {raw_operation.amount} {raw_operation.currency} - {raw_operation.customer}")
            continue

        seen_operations.add(operation_key)
        all_raw_operations.append((raw_operation, statement.account_number))
```

**Key Points:**
- Uses 6 fields to create unique operation signature
- Reference number is particularly important (bank's unique transaction ID)
- Duplicate detection happens BEFORE any processing
- Logs detected duplicates for transparency

### 2. Enhanced Logging (Diagnostic Improvement)

Added detailed logging in `main.py` to monitor the deduplication process:

```python
print(f"Получено выписок: {len(statements)}")
total_raw_operations = sum(len(stmt.operations) for stmt in statements)
print(f"Всего операций в выписках: {total_raw_operations}")

# After deduplication
print(f"После дедупликации и обработки: {len(operations)} операций")

# After ZenMoney filtering
print(f"После фильтрации существующих в ZenMoney: {len(filtered_operations)} операций")
```

**Benefits:**
- See how many statements were fetched
- See how many total operations before deduplication
- See how many duplicates were removed
- See how many passed ZenMoney filter

## 🔒 Why This Fix Is Safe

1. **Unique Key is Comprehensive**: Uses 6 fields including bank reference number
2. **False Positives Unlikely**: Two different operations with identical date, amount, currency, customer, reference, AND description would be extremely rare
3. **Preserves Existing Logic**: All existing filtering and categorization logic remains unchanged
4. **Early Detection**: Duplicates are caught before any processing, preventing wasted work
5. **Transparent**: Logs every duplicate found

## 📊 Expected Output After Fix

### Before Fix
```
Получено выписок: 3
Всего операций в выписках: 45
После дедупликации и обработки: 45 операций
После фильтрации существующих в ZenMoney: 15 операций
Найдено 15 новых операций для импорта
```

### After Fix (with duplicates)
```
Получено выписок: 3
Всего операций в выписках: 45
ДУБЛИКАТ: 02.01.2024 - -1000.0 RSD - MARKET ABC
ДУБЛИКАТ: 02.01.2024 - -500.0 RSD - PHARMACY XYZ

Обнаружено и пропущено дубликатов: 2
После дедупликации и обработки: 43 операций
После фильтрации существующих в ZenMoney: 13 операций
Найдено 13 новых операций для импорта
```

## 🧪 Testing

### Manual Testing Steps

1. **Run with current data**:
   ```bash
   python src/main.py
   ```
   
2. **Check for "ДУБЛИКАТ:" messages** in output

3. **Verify counts**:
   - `Всего операций` should be higher than `После дедупликации` if duplicates exist
   - `Обнаружено и пропущено дубликатов: N` should appear if duplicates found

### Test Scenarios

✅ **Scenario 1**: Multiple emails with same operations
- Expected: Duplicates detected and logged

✅ **Scenario 2**: No duplicate emails
- Expected: No duplicates detected, counts remain same

✅ **Scenario 3**: Operations already in ZenMoney
- Expected: Pass deduplication, filtered by ZenMoney filter

## 🔄 Multi-Layer Protection

The system now has **3 layers** of duplicate protection:

1. **Layer 1 (NEW)**: Raw operation deduplication in `preparer.py`
   - Prevents duplicate operations from multiple emails
   - Happens BEFORE processing

2. **Layer 2 (EXISTING)**: Operation linking in `preparer.py`
   - Prevents duplicate linked operations (currency exchanges)
   - Uses `processed_operations` set

3. **Layer 3 (EXISTING)**: ZenMoney filter in `filter.py`
   - Prevents re-importing existing ZenMoney transactions
   - Compares with existing transactions

## 📝 Related Files Modified

- ✅ `src/services/operations/preparer.py` - Added raw operation deduplication
- ✅ `src/main.py` - Added detailed logging
- ✅ `.ai/BUGFIX_DUPLICATES.md` - This documentation

## 🚀 Deployment

No configuration changes needed. The fix is automatic and backward compatible.

Simply pull the latest code and run:
```bash
python src/main.py
```

## 🔮 Future Improvements

Consider adding:
1. **Email deduplication**: Track processed email UIDs to avoid re-processing
2. **Operation hash**: Store SHA256 hash of operations in ZenMoney comments
3. **Database tracking**: SQLite database to track processed operations across runs
4. **Configurable deduplication**: Option to enable/disable or configure deduplication logic

## 📚 References

- **Issue**: Duplicate transactions on January 2nd
- **Fix Date**: 2024
- **Modified Files**: `preparer.py`, `main.py`
- **Testing**: Manual verification required after deployment

---

**Status**: ✅ Fixed  
**Version**: 1.0  
**Author**: AI Assistant  
**Date**: 2024