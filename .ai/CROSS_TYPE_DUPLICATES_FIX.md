# Исправление кросс-типных дубликатов операций

## Проблема

Одна и та же операция банка могла импортироваться дважды в ZenMoney как разные типы операций:

**Пример с 14 февраля 2026:**
- **Операция 1:** SimpleOperation - "Импорт: RAIFFEISEN BANKA (RSD)" - 97566 RSD пополнение
- **Операция 2:** TransitionOperation - "Обмен валют: -97566 RSD → +97566 RSD" - 97566 RSD обмен

Это происходило потому что фильтр проверял дубликаты по типу операции и комментарию, но не по идентификатору банковской операции.

### Когда это происходило

1. **Первый запуск:** Приходит SMS уведомление с операцией без полной информации о валютном обмене
   - Классифицируется как SimpleOperation (простой платеж)
   - Импортируется в ZenMoney

2. **Второй запуск:** Приходит полная выписка со всеми деталями
   - Система видит две связанные операции разных валют с ключевым словом "po kursu" (по курсу)
   - Классифицирует как TransitionOperation (обмен валюты)
   - Снова импортирует в ZenMoney

3. **Результат:** Две операции в ZenMoney для одного банковского платежа ❌

## Решение

### 1. Добавлено отслеживание банковских ссылок (Reference)

Все типы операций теперь содержат поле `reference`:

```python
@dataclass
class SimpleOperation:
    reference: str = ""

@dataclass
class TransitionOperation:
    from_reference: str = ""
    to_reference: str = ""

@dataclass  
class DeelTransferOperation:
    reference: str = ""

@dataclass
class CashWithdrawalOperation:
    reference: str = ""
```

### 2. Добавлены ссылки в комментарии ZenMoney

Теперь комментарии содержат банковский идентификатор ссылки:

```
Старо: "Импорт: RAIFFEISEN BANKA (RSD)"
Ново: "Импорт: RAIFFEISEN BANKA (RSD) [Ref: 97566RSD]"

Старо: "Обмен валют: -100 USD → +12000 RSD"  
Ново: "Обмен валют: -100 USD → +12000 RSD [Refs: REF1,REF2]"

Старо: "Transfer from Deel: Name"
Ново: "Transfer from Deel: Name [Ref: DEEL123]"

Старо: "Снятие наличных: ATM 123"
Ново: "Снятие наличных: ATM 123 [Ref: ATM456]"
```

### 3. Улучшена логика фильтрации

Filter теперь:

1. **Извлекает ссылки** из существующих транзакций в ZenMoney
2. **Проверяет по ссылке** перед импортом новой операции
3. **Пропускает** операцию если её ссылка уже импортирована (любого типа)

```python
# В filter.py добавлена функция
def _extract_reference_from_comment(comment: str | None) -> str:
    """Извлекает ссылку из комментария в формате [Ref: XXXXX]"""
    
# Перед импортом любой операции проверяется
if operation.reference and operation.reference in existing_references:
    print(f"⚠️ ДУБЛИКАТ ПО REFERENCE: ... (уже импортирована как другой тип)")
    continue  # Пропуск импорта
```

## Как это работает

### До исправления

```
Email 1 (SMS): 
  Op: +97566 RSD
  ↓
  SimpleOperation
  ↓
  Импортируется в ZenMoney ✅

Email 2 (Выписка):
  Op1: -97566 RSD (description: "po kursu")
  Op2: +97566 RSD
  ↓
  TransitionOperation (видит разные валюты и ключевое слово)
  ↓
  Импортируется в ZenMoney ✅ (ДУБЛИКАТ!)

Результат: 2 транзакции ❌
```

### После исправления

```
Email 1 (SMS):
  Op: +97566 RSD [Ref: 97566RSD]
  ↓
  SimpleOperation with reference="97566RSD"
  ↓
  Comment: "Импорт: ... [Ref: 97566RSD]"
  ↓
  Импортируется в ZenMoney ✅

Email 2 (Выписка):
  Op1: -97566 RSD [Ref: 97566RSD]
  Op2: +97566 RSD [Ref: 97566RSD]
  ↓
  TransitionOperation with references
  ↓
  Фильтр: "97566RSD уже импортирована!"
  ↓
  Пропускается ✅ (ДУБЛИКАТ ПРЕДОТВРАЩЕН!)

Результат: 1 транзакция ✅
```

## Файлы с изменениями

- `src/services/operations/operations.py` - Добавлены поля reference
- `src/services/zen_money/preparer.py` - Добавлены ссылки в комментарии
- `src/services/operations/filter.py` - Добавлена проверка по ссылкам

## Преимущества

✅ Предотвращает кросс-типные дубликаты (SimpleOperation ≠ TransitionOperation)  
✅ Работает даже если одна операция приходит в разных формах  
✅ Простое и надёжное решение (на основе уникальных ID банка)  
✅ Не требует изменения структуры баз данных  
✅ Обратно совместимо (старые операции тоже будут проверяться)

## Примечание

Старые операции в ZenMoney (импортированные до этого исправления) уже содержат дубликаты. 

**Система автоматически удаляет дубликаты при каждом запуске** через функцию `auto_cleanup_duplicates()` в `src/services/zen_money/auto_cleanup.py`.

Если вы хотите вручную очистить старые дубликаты, используйте:
```bash
uv run python cleanup_sms_duplicates.py --auto-confirm
```

## Версия

- **Дата:** Февраль 2026
- **Статус:** ✅ В работе
- **Исправляет:** Issue с 97566 RSD от 14 февраля
