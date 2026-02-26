# Архитектура импорта операций

## Общий поток данных

```
ИСТОЧНИК 1: SMS от банка Raiffeisen
  ↓
  Автоматически добавляется в ZenMoney через встроенную интеграцию
  Операция: простая (без деталей о валютном обмене)
  Комментарий: может быть пусто, "Пополнение", "Платеж" и т.д.
  Reference: может отсутствовать
  ↓
  ZenMoney (потенциально неполная/неточная информация)

ИСТОЧНИК 2: XML выписки от Raiffeisen  
  ↓
  Получены по email (вложения)
  Распарсены через `src/services/emails_statements/getter.py`
  Содержат полную информацию с деталями и reference (Referenca)
  ↓
  Обработаны скриптом раiffeisen_to_zenmoney
  - Дедупликация на уровне raw операций
  - Классификация (SimpleOperation / TransitionOperation / Deel / CashWithdrawal)
  - Фильтрация (не добавлять уже существующие)
  - Добавление в ZenMoney
  ↓
  ZenMoney (полная и точная информация)
```

## Проблема: Cross-type дубликаты

### Сценарий 97566 RSD (14 февраля 2026)

```
Время T1: SMS от Raiffeisen о платеже 97566 RSD
  → Автоматически добавлено в ZenMoney
  → Операция: income 97566 RSD
  → Payee: название получателя или пусто
  → Comment: (пусто или "Пополнение")
  → СОЗДАНА: ZenMoney транзакция #1

Время T2: XML выписка содержит:
  Op1: -97566 RSD (outcome, description: "po kursu")
  Op2: +97566 RSD (income)
  → Скрипт видит: разные валюты + ключевое слово "po kursu"
  → Классифицирует как: TransitionOperation (обмен валюты)
  → Добавляет в ZenMoney
  → СОЗДАНА: ZenMoney транзакция #2

РЕЗУЛЬТАТ: Две транзакции в ZenMoney для одного платежа ❌
```

## Решение

### Двухуровневая защита

#### Уровень 1: Reference tracking (для дубликатов из выписок)

Применяется когда: **одна операция импортируется дважды через скрипт**

```python
# В operations.py - все операции содержат reference
@dataclass
class SimpleOperation:
    reference: str = ""  # Bank reference ID from "Referenca"

@dataclass
class TransitionOperation:
    from_reference: str = ""
    to_reference: str = ""
```

```python
# В preparer.py - reference добавляется в комментарий
comment = f"Импорт: {customer} ({currency}) [Ref: {reference}]"
comment = f"Обмен валют: {from} → {to} [Refs: {ref1},{ref2}]"
```

```python
# В filter.py - проверяется по reference перед импортом
if operation.reference in existing_references:
    # Пропустить - уже импортирована
    continue
```

**Работает для:** Случаев когда одна XML выписка обрабатывается дважды

---

#### Уровень 2: Cross-type detection (для SMS vs Import)

Применяется когда: **SMS добавляет простую операцию, выписка добавляет полную**

```python
# В auto_cleanup.py - обнаруживает кросс-типные дубликаты
def find_duplicate_transactions():
    # Групповые операции по типам:
    sms_groups = {}      # SMS от банка (comment не начинается с "Импорт:")
    import_groups = {}   # Из выписки (comment начинается с "Импорт:/Обмен:")
    cross_type = []      # SMS + Import с одинаковыми date/amount/currency
    
    # Для каждой пары SMS + Import с одинаковыми параметрами:
    # УДАЛИТЬ SMS версию, ОСТАВИТЬ Import (более полная)
```

**Работает для:** SMS от банка + XML выписка с одним платежом

---

### Автоматическое выполнение

```python
# В main.py - запускается в начале каждой синхронизации
def main():
    print("Проверка и удаление дубликатов...")
    cleanup_result = auto_cleanup_duplicates(DAYS)
    # Затем импортируются новые операции...
```

## Файлы и их роль

### Парсинг и классификация
- `src/services/emails_statements/getter.py` - получение XML из email
- `src/services/emails_statements/statement.py` - парсинг XML → RawOperation
- `src/services/operations/operations.py` - классификация (SimpleOp/TransitionOp/etc)
- `src/services/operations/preparer.py` - преобразование в ZenMoney транзакции

### Дедупликация и фильтрация
- `src/services/operations/filter.py` - reference-based filtering (Уровень 1)
- `src/services/zen_money/auto_cleanup.py` - cross-type detection (Уровень 2) ⭐

### Синхронизация
- `src/main.py` - запуск auto-cleanup + импорт + фильтрация
- `src/services/zen_money/zen_money_api.py` - API к ZenMoney

## Ключевые отличия операций

| Характеристика | SMS (банк) | XML выписка |
|---|---|---|
| **Источник** | Email SMS уведомление | Email XML вложение |
| **Добавляется в ZenMoney** | Автоматически | Через скрипт |
| **Reference** | Может отсутствовать | Всегда есть (Referenca) |
| **Детали** | Минимальные | Полные |
| **Comment** | Пусто или "Пополнение" | "Импорт:", "Обмен валют:", и т.д. |
| **Частота дубликатов** | Высокая | Низкая |

## Дебаг: Как понять, какая операция SMS, какая Import

```python
# SMS операция (из банка)
if not transaction.comment or not transaction.comment.startswith(("Импорт:", "Обмен валют:", "Transfer from", "Снятие")):
    print(f"SMS операция: {transaction.payee} - {transaction.income or transaction.outcome}")

# Import операция (из выписки)
elif transaction.comment.startswith(("Импорт:", "Обмен валют:", "Transfer from", "Снятие")):
    print(f"Import операция: {transaction.comment}")
```

## Примеры дубликатов

### Дубликат 1: Простой платеж

```
SMS: Оплата счёта - 1000 RSD
XML: Импорт: Оплата счёта - 1000 RSD [Ref: INV123]
→ Удалить SMS, оставить XML ✅
```

### Дубликат 2: Обмен валюты

```
SMS: Пополнение - 100 USD (SMS уведомление не содержит info об обмене)
XML: Обмен валют: -100 USD → +12000 RSD [Refs: EUR123,RSD456]
→ Удалить SMS, оставить XML (полную информацию об обмене) ✅
```

### Дубликат 3: Снятие наличных

```
SMS: Снятие - 500 RSD
XML: Снятие наличных: ATM №456 - 500 RSD [Ref: ATM789]
→ Удалить SMS, оставить XML ✅
```

## Версии исправлений

- **v1.0** (2026-02-25): Добавлен reference tracking + cross-type detection
  - Исправляет: 97566 RSD от 14 февраля
  - Предотвращает: будущие кросс-типные дубликаты
  - Удаляет: старые дубликаты автоматически

