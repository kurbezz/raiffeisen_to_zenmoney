# Codebase Context: Raiffeisen to ZenMoney

**Version:** 1.0  
**Purpose:** Detailed implementation context for AI agents working with the codebase

---

## 📋 Table of Contents

1. [Module Deep Dive](#module-deep-dive)
2. [Code Examples](#code-examples)
3. [Data Structures](#data-structures)
4. [Business Logic](#business-logic)
5. [Integration Details](#integration-details)
6. [Common Patterns](#common-patterns)
7. [Testing Considerations](#testing-considerations)

---

## Module Deep Dive

### Configuration Module (`src/config.py`)

**File Size:** ~4KB  
**Complexity:** Low  
**Dependencies:** `pathlib`, `yaml`

**Class: Config**

```python
class Config:
    def __init__(self, config_path: str | None = None):
        # Defaults to parent/config.yaml
        # Loads YAML into self._config dict
    
    def get(self, key: str, default: Any = None) -> Any:
        # Supports dot notation: "email.username"
        # Traverses nested dicts
    
    @property
    def email_username(self) -> str:
        # Convenience accessors
```

**Key Points:**
- Singleton pattern via `get_config()`
- Lazy loading (only loads once)
- Dot notation for nested keys
- Type hints for all methods
- No validation (relies on YAML structure)

**Example Usage:**
```python
from config import get_config

config = get_config()
api_key = config.zen_money_api_key
# or
api_key = config.get("zen_money.api_key")
# or
api_key = config["zen_money.api_key"]
```

**Configuration File Location:**
- Development: `./config.yaml`
- Resolved from: `Path(__file__).parent.parent / "config.yaml"`

---

### Environment Bridge (`src/envs.py`)

**File Size:** ~1KB  
**Complexity:** Low  
**Dependencies:** `config`

**Purpose:**
- Backward compatibility layer
- Imports from `config.py`
- Exposes as module-level constants

**Exported Constants:**
```python
EMAIL_USERNAME: str
EMAIL_PASSWORD: str
EMAIL_ALLOWED_SUBJECTS: list[str]
ZEN_MONEY_API_KEY: str
USER_ID: int
CURRENCY_CONFIG: Dict[str, Any]
CATEGORY_CONFIG: Dict[str, str]
DEEL_CONFIG: Dict[str, Any]
```

**Usage Pattern:**
```python
# Old code can still import from envs
from envs import EMAIL_USERNAME, ZEN_MONEY_API_KEY

# New code should use config module
from config import get_config
```

---

### Main Entry Point (`src/main.py`)

**File Size:** ~2KB  
**Complexity:** Medium  
**Dependencies:** All service modules

**Function: main()**

**Flow:**
1. Set `DAYS = 7` (configurable constant)
2. `get_statements(DAYS)` → Statement[]
3. `get_state(DAYS)` → ZenMoneyState
4. `prepare_operations(statements, deel_config)` → Operation[]
5. `filter_operations(operations, zen_money_state)` → Operation[]
6. If operations exist:
   - Print summary with operation details
   - `prepare_new_state(operations)` → NewZenMoneyState
   - `update_state(new_state)`
   - Print success message
7. Else: Print "no new operations"

**Console Output:**
```
Найдено N новых операций для импорта

Новые операции:
1. 2024-01-15 - 100.00 USD - Customer Name
2. [DEEL] 2024-01-16 - 5000.00 USD - DEEL INC
3. 2024-01-17 - 500.00 RSD → 50.00 USD

Операции успешно импортированы!
```

**Error Handling:**
- None explicit (exceptions propagate)
- API errors raise in `update_state()`
- Email errors raise in `get_statements()`

---

### Email Statements Module

#### `services/emails_statements/getter.py`

**File Size:** ~1.5KB  
**Complexity:** Medium  
**Dependencies:** `imapclient`, `mailparser`, `base64`, `datetime`

**Function: get_statements(days: int = 1) -> list[Statement]**

**Detailed Implementation:**

```python
def get_statements(days: int = 1) -> list[Statement]:
    # 1. Connect to Gmail IMAP
    server = IMAPClient("imap.gmail.com", use_uid=True, ssl=True)
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    server.select_folder("INBOX")
    
    # 2. Calculate date range
    since_date = (date.today() - timedelta(days=days)).strftime("%d-%b-%Y")
    
    # 3. Search for Raiffeisen emails
    messages = server.search(
        f'(FROM "RaiffeisenOnline@raiffeisenbank.rs" SINCE {since_date})'
    )
    
    # 4. Process each email
    statements = []
    for _uid, message_data in server.fetch(messages, "RFC822").items():
        mail = mailparser.parse_from_bytes(message_data[b"RFC822"])
        
        # 5. Filter by subject
        if mail.subject not in EMAIL_ALLOWED_SUBJECTS:
            continue
        
        # 6. Extract XML attachments
        for attachment in mail.attachments:
            if not attachment.get("filename", "").lower().endswith(".xml"):
                continue
            
            payload = attachment.get("payload")
            if not payload:
                continue
            
            # 7. Decode and parse XML
            xml_content = base64.b64decode(payload).decode()
            statements.append(Statement.from_xml(xml_content))
    
    return statements
```

**IMAP Details:**
- Server: `imap.gmail.com`
- Port: 993 (SSL)
- Search syntax: RFC 3501
- Date format: `DD-MMM-YYYY` (e.g., `01-Jan-2024`)

**Email Filter:**
- FROM: `RaiffeisenOnline@raiffeisenbank.rs`
- SINCE: calculated date
- SUBJECT: must be in `EMAIL_ALLOWED_SUBJECTS`

**Attachment Handling:**
- Only `.xml` files processed
- Base64 encoded in email
- Decoded to UTF-8 string

---

#### `services/emails_statements/statement.py`

**File Size:** ~3KB  
**Complexity:** High  
**Dependencies:** `lxml`, `pydantic`

**Models:**

```python
class RawOperation(BaseModel):
    customer: str          # Payee/merchant name
    amount: float          # Positive = income, negative = expense
    currency: str          # "USD", "RSD", etc.
    data: str              # Date in YYYY-MM-DD format
    description: str       # Full transaction description
    reference: str         # Reference number for linking

class Statement(BaseModel):
    account_number: str    # Bank account number
    currency: str          # Account currency
    operations: list[RawOperation]  # All transactions
    
    @classmethod
    def from_xml(cls, xml_content: str) -> "Statement":
        # Parse XML and create Statement
```

**XML Schema (Raiffeisen Bank Serbia):**

```xml
<statement>
    <account_number>123456789</account_number>
    <currency>USD</currency>
    <operations>
        <operation>
            <customer>Customer Name</customer>
            <amount>100.00</amount>
            <currency>USD</currency>
            <date>2024-01-15</date>
            <description>Payment description</description>
            <reference>REF123456</reference>
        </operation>
        <!-- More operations -->
    </operations>
</statement>
```

**XML Parsing Implementation:**

```python
from lxml import etree

@classmethod
def from_xml(cls, xml_content: str) -> "Statement":
    root = etree.fromstring(xml_content.encode())
    
    # Extract account info
    account_number = root.find(".//account_number").text
    currency = root.find(".//currency").text
    
    # Parse operations
    operations = []
    for op_elem in root.findall(".//operation"):
        operation = RawOperation(
            customer=op_elem.find("customer").text or "",
            amount=float(op_elem.find("amount").text or 0),
            currency=op_elem.find("currency").text or "",
            data=op_elem.find("date").text or "",
            description=op_elem.find("description").text or "",
            reference=op_elem.find("reference").text or ""
        )
        operations.append(operation)
    
    return cls(
        account_number=account_number,
        currency=currency,
        operations=operations
    )
```

**Key Behaviors:**
- XPath-style element finding
- Default values for missing elements
- Type coercion (str → float for amount)
- Pydantic validation after creation

---

### Operations Module

#### `services/operations/operations.py`

**File Size:** ~1.5KB  
**Complexity:** Low  
**Dependencies:** `dataclasses`, `typing`

**All operations are dataclasses (not Pydantic):**

```python
from dataclasses import dataclass
from typing import Self

@dataclass
class SimpleOperation:
    customer: str
    amount: float
    currency: str
    date: str
    
    @classmethod
    def from_raw(cls, raw_operation: RawOperation) -> Self:
        return cls(
            customer=raw_operation.customer,
            amount=raw_operation.amount,
            currency=raw_operation.currency,
            date=raw_operation.data,  # Note: 'data' field maps to 'date'
        )
```

**Operation Types:**

1. **SimpleOperation** - Single transaction
   - Income: amount > 0
   - Expense: amount < 0
   - Maps to single ZenMoney transaction

2. **TransitionOperation** - Currency exchange
   - Two linked operations
   - Different currencies
   - Opposite signs
   - Maps to transfer transaction

3. **DeelTransferOperation** - Deel payment
   - Incoming transfer (amount > 0)
   - Matches Deel keywords
   - Maps to transfer from Deel account

**Factory Pattern:**
- All use `@classmethod from_raw()`
- Accepts RawOperation(s)
- Returns typed operation

---

#### `services/operations/preparer.py`

**File Size:** ~4KB  
**Complexity:** High  
**Dependencies:** `operations`, `statement`

**Function: prepare_operations(statements, deel_config)**

**Algorithm Breakdown:**

**Phase 1: Collect all operations**
```python
all_raw_operations = []
for statement in statements:
    for raw_operation in statement.operations:
        all_raw_operations.append((raw_operation, statement.account_number))
```

**Phase 2: Link currency exchanges**
```python
processed_operations = set()  # Track by id(operation)

for i, (op1, acc1) in enumerate(all_raw_operations):
    if id(op1) in processed_operations:
        continue
    
    for j, (op2, acc2) in enumerate(all_raw_operations[i + 1:], i + 1):
        if id(op2) in processed_operations:
            continue
        
        # Check if linked
        if _are_operations_linked(op1, op2):
            # Check if currency exchange
            if (op1.currency != op2.currency and
                (op1.amount < 0 and op2.amount > 0 or 
                 op1.amount > 0 and op2.amount < 0) and
                (_is_currency_exchange(op1) or _is_currency_exchange(op2))):
                
                # Determine direction (from negative to positive)
                if op1.amount < 0:
                    from_op, to_op = op1, op2
                else:
                    from_op, to_op = op2, op1
                
                # Create transition
                transition_op = TransitionOperation.from_raw(from_op, to_op)
                operations.append(transition_op)
                
                # Mark both as processed
                processed_operations.add(id(op1))
                processed_operations.add(id(op2))
                break
```

**Phase 3: Process remaining operations**
```python
for raw_operation, account_number in all_raw_operations:
    if id(raw_operation) not in processed_operations:
        # Check Deel transfer
        if deel_config and _is_deel_transfer(raw_operation, deel_config):
            deel_op = DeelTransferOperation.from_raw(raw_operation)
            operations.append(deel_op)
        else:
            simple_op = SimpleOperation.from_raw(raw_operation)
            operations.append(simple_op)
```

**Helper Functions:**

**_are_operations_linked(op1, op2) -> bool**
```python
# Method 1: Same reference number
if op1.reference and op2.reference and op1.reference == op2.reference:
    return True

# Method 2: Reference in description
if op1.reference and op1.reference in op2.description:
    return True
if op2.reference and op2.reference in op1.description:
    return True

return False
```

**_is_currency_exchange(operation) -> bool**
```python
description_lower = operation.description.lower()
customer_lower = operation.customer.lower()

exchange_keywords = [
    "otkup",
    "kupoprodaja deviza",
    "dinarska protivvrednost",
    "po kursu",
    "protivvrednost",
]

return (
    any(keyword in description_lower for keyword in exchange_keywords) or
    "raiffeisen banka" in customer_lower
)
```

**_is_deel_transfer(operation, deel_config) -> bool**
```python
# Must be enabled
if not deel_config.get("enabled", False):
    return False

# Must be incoming
if operation.amount <= 0:
    return False

# Check keywords
keywords = deel_config.get("keywords", [])
if not keywords:
    return False

customer_lower = operation.customer.lower()
description_lower = operation.description.lower()

for keyword in keywords:
    keyword_lower = keyword.lower()
    if keyword_lower in customer_lower or keyword_lower in description_lower:
        return True

return False
```

---

#### `services/operations/filter.py`

**File Size:** ~2KB  
**Complexity:** Medium  
**Dependencies:** `operations`, `zen_money_api`

**Function: filter_operations(operations, zen_money_state) -> list[Operation]**

**Duplicate Detection Logic:**

```python
def filter_operations(operations, zen_money_state):
    filtered = []
    
    for operation in operations:
        is_duplicate = False
        
        for transaction in zen_money_state.transaction:
            if _is_duplicate(operation, transaction):
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered.append(operation)
    
    return filtered
```

**_is_duplicate(operation, transaction) -> bool**

**For SimpleOperation:**
```python
# Check date
if operation.date != transaction.date:
    return False

# Check amount (absolute value)
if abs(operation.amount) != abs(transaction.income - transaction.outcome):
    return False

# Check payee (case-insensitive substring)
if transaction.payee:
    if operation.customer.lower() not in transaction.payee.lower() and \
       transaction.payee.lower() not in operation.customer.lower():
        return False

return True
```

**For TransitionOperation:**
```python
# Check both amounts
from_amount_match = abs(operation.from_amount) == abs(transaction.outcome)
to_amount_match = abs(operation.to_amount) == abs(transaction.income)

# Check date
date_match = operation.date == transaction.date

return from_amount_match and to_amount_match and date_match
```

**For DeelTransferOperation:**
```python
# Similar to SimpleOperation but checks transfer accounts
# Must match Deel account ID in outcomeAccount
```

---

### ZenMoney Module

#### `services/zen_money/zen_money_api.py`

**File Size:** ~8KB  
**Complexity:** High  
**Dependencies:** `pydantic`, `requests`, `datetime`

**Pydantic Models:**

All models inherit from `BaseModel` with:
- Camel case field names (matching API)
- Optional fields with `Optional[T] = None`
- Type validation
- JSON serialization/deserialization

**Key Models:**

```python
class Instrument(BaseModel):
    id: int                    # Currency ID
    title: str                 # Full name
    shortTitle: str            # Abbreviation
    symbol: str                # Currency symbol
    rate: float                # Exchange rate
    changed: int               # Last modified timestamp

class Account(BaseModel):
    id: str                    # UUID
    user: int                  # User ID
    instrument: int            # Currency ID
    type: str                  # "cash", "ccard", "checking", etc.
    title: str                 # Account name
    balance: float             # Current balance
    # ... 20+ more fields

class Transaction(BaseModel):
    id: str                    # UUID
    user: int                  # User ID
    date: str                  # YYYY-MM-DD
    income: float              # Incoming amount
    outcome: float             # Outgoing amount
    incomeInstrument: int      # Currency ID for income
    outcomeInstrument: int     # Currency ID for outcome
    incomeAccount: str         # Account UUID for income
    outcomeAccount: str        # Account UUID for outcome (optional for income)
    created: int               # Creation timestamp
    changed: int               # Last modified timestamp
    deleted: bool              # Soft delete flag
    viewed: bool               # User has seen it
    payee: Optional[str]       # Payee name
    comment: Optional[str]     # User comment
    tag: Optional[List[str]]   # Category tags
    # ... more optional fields
```

**API Functions:**

**get_state(days: int) -> ZenMoneyState**

```python
def get_state(days: int) -> ZenMoneyState:
    # Current timestamp
    currentTimestamp = int(datetime.today().timestamp())
    
    # Server timestamp (N days ago, start of day)
    serverTimestamp = int(
        (datetime.today() - timedelta(days=days))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    
    # API request
    r = requests.post(
        "https://api.zenmoney.ru/v8/diff/",
        headers={"Authorization": f"Bearer {ZEN_MONEY_API_KEY}"},
        json={
            "currentClientTimestamp": currentTimestamp,
            "serverTimestamp": serverTimestamp,
        },
    )
    
    # Error handling
    if r.status_code != 200:
        raise Exception(f"Error: {r.status_code} {r.text}")
    
    # Parse response
    return ZenMoneyState.model_validate(r.json())
```

**update_state(state: NewZenMoneyState) -> dict**

```python
def update_state(state: NewZenMoneyState):
    # Prepare data (remove None fields)
    data = state.model_dump()
    
    entity_fields = [
        "instrument",
        "account",
        "budget",
        "reminder",
        "reminderMarker",
        "deletion",
    ]
    for field in entity_fields:
        if field in data and data[field] is None:
            del data[field]
    
    # API request
    r = requests.post(
        "https://api.zenmoney.ru/v8/diff/",
        headers={"Authorization": f"Bearer {ZEN_MONEY_API_KEY}"},
        json=data,
    )
    
    # Error handling
    if r.status_code != 200:
        raise Exception(f"Error updating state: {r.status_code} {r.text}")
    
    return r.json()
```

**API Behavior:**
- Diff-based sync (only send changes)
- Server merges changes with current state
- Timestamps track sync state
- All entities have `changed` field

---

#### `services/zen_money/preparer.py`

**File Size:** ~3KB  
**Complexity:** High  
**Dependencies:** `operations`, `zen_money_api`, `config`, `uuid`, `datetime`

**Function: prepare_new_state(operations) -> NewZenMoneyState**

**Implementation:**

```python
from uuid import uuid4
from datetime import datetime
from envs import USER_ID, CURRENCY_CONFIG, CATEGORY_CONFIG

def prepare_new_state(operations):
    transactions = []
    current_timestamp = int(datetime.now().timestamp())
    
    for operation in operations:
        if isinstance(operation, SimpleOperation):
            transaction = _create_simple_transaction(operation, current_timestamp)
        elif isinstance(operation, TransitionOperation):
            transaction = _create_transition_transaction(operation, current_timestamp)
        elif isinstance(operation, DeelTransferOperation):
            transaction = _create_deel_transaction(operation, current_timestamp)
        
        transactions.append(transaction)
    
    return NewZenMoneyState(
        currentClientTimestamp=current_timestamp,
        serverTimestamp=0,  # Will be set by API
        transaction=transactions
    )
```

**_create_simple_transaction(operation, timestamp)**

```python
def _create_simple_transaction(operation, timestamp):
    # Get currency config
    currency_cfg = CURRENCY_CONFIG.get(operation.currency, {})
    instrument_id = currency_cfg.get("instrument_id")
    account_id = currency_cfg.get("account_id")
    cash_account_id = currency_cfg.get("cash_account_id")
    
    # Determine income/outcome based on amount sign
    if operation.amount > 0:
        # Income to account
        income = operation.amount
        outcome = operation.amount
        income_account = account_id
        outcome_account = cash_account_id
    else:
        # Expense from account
        income = abs(operation.amount)
        outcome = abs(operation.amount)
        income_account = cash_account_id
        outcome_account = account_id
    
    # Find category by merchant name
    category_tag = None
    for merchant, category_uuid in CATEGORY_CONFIG.items():
        if merchant.lower() in operation.customer.lower():
            category_tag = [category_uuid]
            break
    
    # Create transaction
    return Transaction(
        id=str(uuid4()),
        user=USER_ID,
        date=operation.date,
        income=income,
        outcome=outcome,
        incomeInstrument=instrument_id,
        outcomeInstrument=instrument_id,
        incomeAccount=income_account,
        outcomeAccount=outcome_account,
        created=timestamp,
        changed=timestamp,
        deleted=False,
        viewed=False,
        payee=operation.customer,
        comment=None,
        tag=category_tag,
    )
```

**_create_transition_transaction(operation, timestamp)**

```python
def _create_transition_transaction(operation, timestamp):
    # Get config for both currencies
    from_cfg = CURRENCY_CONFIG.get(operation.from_currency, {})
    to_cfg = CURRENCY_CONFIG.get(operation.to_currency, {})
    
    # Create transfer transaction
    return Transaction(
        id=str(uuid4()),
        user=USER_ID,
        date=operation.date,
        income=abs(operation.to_amount),
        outcome=abs(operation.from_amount),
        incomeInstrument=to_cfg.get("instrument_id"),
        outcomeInstrument=from_cfg.get("instrument_id"),
        incomeAccount=to_cfg.get("account_id"),
        outcomeAccount=from_cfg.get("account_id"),
        opIncome=abs(operation.to_amount),    # Original amounts
        opOutcome=abs(operation.from_amount),
        opIncomeInstrument=to_cfg.get("instrument_id"),
        opOutcomeInstrument=from_cfg.get("instrument_id"),
        created=timestamp,
        changed=timestamp,
        deleted=False,
        viewed=False,
        payee="Currency Exchange",
        comment=f"{operation.from_currency} → {operation.to_currency}",
    )
```

**_create_deel_transaction(operation, timestamp)**

```python
def _create_deel_transaction(operation, timestamp):
    from envs import DEEL_CONFIG
    
    # Get config
    deel_account_id = DEEL_CONFIG.get("account_id")
    bank_cfg = CURRENCY_CONFIG.get(operation.currency, {})
    
    # Create transfer from Deel to bank
    return Transaction(
        id=str(uuid4()),
        user=USER_ID,
        date=operation.date,
        income=operation.amount,
        outcome=operation.amount,
        incomeInstrument=bank_cfg.get("instrument_id"),
        outcomeInstrument=bank_cfg.get("instrument_id"),
        incomeAccount=bank_cfg.get("account_id"),
        outcomeAccount=deel_account_id,
        created=timestamp,
        changed=timestamp,
        deleted=False,
        viewed=False,
        payee="Deel Transfer",
        comment=f"Transfer from Deel: {operation.customer}",
    )
```

---

## Code Examples

### Complete Flow Example

```python
# 1. Fetch statements
statements = get_statements(7)
# Returns: [Statement(account_number="123", currency="USD", operations=[...])]

# 2. Get ZenMoney state
zen_state = get_state(7)
# Returns: ZenMoneyState(transaction=[...], account=[...], ...)

# 3. Prepare operations
operations = prepare_operations(statements, DEEL_CONFIG)
# Returns: [SimpleOperation(...), TransitionOperation(...), ...]

# 4. Filter duplicates
new_operations = filter_operations(operations, zen_state)
# Returns: operations not in zen_state.transaction

# 5. Prepare API payload
new_state = prepare_new_state(new_operations)
# Returns: NewZenMoneyState(transaction=[Transaction(...), ...])

# 6. Sync to API
result = update_state(new_state)
# POSTs to ZenMoney API
```

### Adding Custom Operation Type

```python
# Step 1: Define model
@dataclass
class CustomOperation:
    field1: str
    field2: float
    date: str
    
    @classmethod
    def from_raw(cls, raw: RawOperation) -> Self:
        return cls(
            field1=raw.customer,
            field2=raw.amount,
            date=raw.data
        )

# Step 2: Add detection in preparer.py
def _is_custom_operation(operation: RawOperation) -> bool:
    return "CUSTOM_KEYWORD" in operation.description.upper()

# Step 3: Add to prepare_operations
if _is_custom_operation(raw_operation):
    custom_op = CustomOperation.from_raw(raw_operation)
    operations.append(custom_op)

# Step 4: Add mapping in zen_money/preparer.py
elif isinstance(operation, CustomOperation):
    transaction = _create_custom_transaction(operation, current_timestamp)
```

---

## Business Logic

### Currency Exchange Detection

**Why:** Banks send two separate operations for currency exchange:
1. Sell operation (negative amount, currency A)
2. Buy operation (positive amount, currency B)

**Solution:** Link by reference number, create TransitionOperation

**Example:**
```
Operation 1: -100.00 USD, ref="EX123"
Operation 2: +11500.00 RSD, ref="EX123"
→ TransitionOperation(from=100 USD, to=11500 RSD)
```

### Deel Transfer Handling

**Why:** Deel payments need to be recorded as transfers between accounts

**Business Rule:**
- Incoming payment from Deel
- Should debit Deel account (virtual)
- Should credit bank account

**Example:**
```
RawOperation: +5000.00 USD, customer="DEEL INC"
→ DeelTransferOperation
→ Transaction(outcomeAccount=deel_account, incomeAccount=bank_account)
```

### Category Assignment

**Why:** Auto-categorize recurring merchants

**Logic:**
- Case-insensitive substring matching
- First match wins
- Categories are UUIDs from ZenMoney

**Example:**
```
category_config:
  "HERMES": "uuid-transport"
  
Operation: customer="HERMES AGENCIJA DOO"
→ tag=["uuid-transport"]
```

---

## Integration Details

### Gmail IMAP

**Connection:**
- Host: `imap.gmail.com`
- Port: 993 (implicit SSL)
- Auth: Username + App Password (not regular password)

**Search Syntax:**
```
(FROM "sender@example.com" SINCE DD-MMM-YYYY)
```

**Attachment Extraction:**
- Use mailparser library
- Attachments are base64 encoded
- Filter by `.xml` extension

### ZenMoney API v8

**Endpoint:** `https://api.zenmoney.ru/v8/diff/`

**Authentication:**
```
Authorization: Bearer YOUR_API_KEY
```

**Request:**
```json
{
  "currentClientTimestamp": 1234567890,
  "serverTimestamp": 1234560000,
  "transaction": [
    {
      "id": "uuid",
      "user": 123,
      "date": "2024-01-15",
      "income": 100.0,
      "outcome": 100.0,
      ...
    }
  ]
}
```

**Response:**
```json
{
  "serverTimestamp": 1234567895,
  "instrument": [...],
  "account": [...],
  "transaction": [...],
  ...
}
```

**Sync Strategy:**
- Diff-based (only changes)
- Server maintains truth
- Client sends updates
- Timestamps track state

---

## Common Patterns

### Pydantic Model Creation

```python
from pydantic import BaseModel
from typing import Optional

class MyModel(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    
    # Validation
    @validator('required_field')
    def validate_field(cls, v):
        if not v:
            raise ValueError('cannot be empty')
        return v
```

### Dataclass with Factory

```python
from dataclasses import dataclass
from typing import Self

@dataclass
class MyOperation:
    field: str
    
    @classmethod
    def from_raw(cls, raw: RawOperation) -> Self:
        return cls(field=raw.field)
```

### Configuration Access

```python
# Modern
from config import get_config
config = get_config()
value = config.get("section.subsection.key", "default")

# Legacy
from envs import CONSTANT_NAME
```

### Error Handling

```python
# Current pattern: let exceptions propagate
def my_function():
    if error_condition:
        raise Exception("Descriptive error message")
    return result
```

---

## Testing Considerations

### Unit Test Targets

1. **Operation Linking Logic**
   - Test `_are_operations_linked()`
   - Edge cases: missing references, partial matches

2. **Currency Exchange Detection**
   - Test `_is_currency_exchange()`
   - Various keyword combinations

3. **Duplicate Detection**
   - Test date/amount/payee matching
   - Edge cases: similar but not duplicate

4. **Transaction Mapping**
   - Test each operation type → Transaction
   - Verify field mapping correctness

### Integration Test Scenarios

1. **Email Fetching**
   - Mock IMAP responses
   - Test attachment extraction

2. **XML Parsing**
   - Valid XML variations
   - Invalid/malformed XML

3. **API Communication**
   - Mock API responses
   - Error handling (401, 400, 500)

### Test Data

**Sample RawOperation:**
```python
RawOperation(
    customer="Test Merchant",
    amount=100.00,
    currency="USD",
    data="2024-01-15",
    description="Payment for services",
    reference="REF123"
)
```

**Sample Statement:**
```python
Statement(
    account_number="123456789",
    currency="USD",
    operations=[raw_op1, raw_op2]
)
```

---

## Performance Considerations

### Email Fetching
- Limited by IMAP connection speed
- Each email requires parse + attachment decode
- Typical: 1-5 emails per run

### XML Parsing
- lxml is fast (C-based)
- Typical XML: < 100KB, < 100 operations
- Parsing time: < 100ms per file

### API Calls
- Two API calls per run:
  1. GET state (fetch existing data)
  2. POST state (send updates)
- Network latency dominant factor
- Typical: 200-500ms per call

### Memory Usage
- All data held in memory
- Typical: < 10MB for 7 days of data
- No pagination needed for current scale

---

## Security Notes

### Sensitive Data

**Never commit:**
- `config.yaml` (credentials, API keys)
- Any file with real account UUIDs
- Email passwords

**Use instead:**
- `config.sample.yaml` (template)
- Environment variables (production)
- Secret management (Docker/K8s)

### Gmail Security

**Best practices:**
- Use app-specific password (not account password)
- Enable 2FA on Gmail account
- Restrict IMAP access if possible

### API Keys

**Best practices:**
- Store only in config file
- Never hardcode in source
- Rotate periodically
- Use read-only keys if available

---

**End of Codebase Context**