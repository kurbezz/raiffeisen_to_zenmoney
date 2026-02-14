# Development Guide: Raiffeisen to ZenMoney

**Version:** 1.0  
**Purpose:** Step-by-step guides for common development tasks

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Adding Transaction Types](#adding-transaction-types)
3. [Modifying Email Processing](#modifying-email-processing)
4. [Adding New Banks](#adding-new-banks)
5. [Custom Categorization Rules](#custom-categorization-rules)
6. [Adding Currency Support](#adding-currency-support)
7. [Debugging Common Issues](#debugging-common-issues)
8. [Testing Changes](#testing-changes)
9. [Configuration Management](#configuration-management)
10. [API Integration](#api-integration)

---

## Getting Started

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd raiffeisen_to_zenmoney

# Install dependencies
uv sync

# Copy configuration template
cp config.sample.yaml config.yaml

# Edit configuration with your credentials
vim config.yaml  # or your preferred editor
```

### Configuration Checklist

**Email Section:**
- [ ] Gmail username
- [ ] App-specific password (not regular password)
- [ ] Allowed email subjects

**ZenMoney Section:**
- [ ] API key from ZenMoney settings
- [ ] User ID from ZenMoney

**Currency Accounts:**
- [ ] For each currency (USD, RSD):
  - [ ] Instrument ID (check ZenMoney)
  - [ ] Account UUID (from ZenMoney URL)
  - [ ] Cash account UUID

**Optional:**
- [ ] Category mappings (merchant → category UUID)
- [ ] Deel configuration (if using Deel)

### First Run

```bash
# Run with default settings (last 7 days)
python src/main.py

# Check output for:
# - Email connection success
# - Statements fetched
# - Operations processed
# - ZenMoney sync status
```

---

## Adding Transaction Types

### Step 1: Define the Operation Model

**File:** `src/services/operations/operations.py`

```python
from dataclasses import dataclass
from typing import Self
from services.emails_statements.statement import RawOperation

@dataclass
class NewOperationType:
    """Description of what this operation represents"""
    
    # Define fields specific to this operation
    field1: str
    field2: float
    currency: str
    date: str
    
    @classmethod
    def from_raw(cls, raw_operation: RawOperation) -> Self:
        """Create from RawOperation"""
        return cls(
            field1=raw_operation.customer,
            field2=raw_operation.amount,
            currency=raw_operation.currency,
            date=raw_operation.data,
        )
```

**Key Points:**
- Use `@dataclass` decorator
- All fields should have type hints
- Implement `from_raw()` classmethod
- Map `raw_operation.data` → `date` (note field name difference)

### Step 2: Add Detection Logic

**File:** `src/services/operations/preparer.py`

Add helper function:

```python
def _is_new_operation_type(operation: RawOperation, config: dict | None = None) -> bool:
    """
    Detect if operation matches new type criteria.
    
    Args:
        operation: Raw operation from bank statement
        config: Optional configuration for detection
    
    Returns:
        True if operation matches this type
    """
    # Example: Check for specific keywords
    keywords = ["KEYWORD1", "KEYWORD2"]
    description_lower = operation.description.lower()
    customer_lower = operation.customer.lower()
    
    for keyword in keywords:
        if keyword.lower() in description_lower or keyword.lower() in customer_lower:
            return True
    
    # Example: Check amount criteria
    if operation.amount > 1000 and "MERCHANT" in customer_lower:
        return True
    
    # Example: Check configuration
    if config and config.get("enabled"):
        # Custom logic based on config
        pass
    
    return False
```

### Step 3: Integrate into Processing Pipeline

**File:** `src/services/operations/preparer.py`

Update `prepare_operations()`:

```python
def prepare_operations(
    statements: list[Statement],
    deel_config: dict | None = None,
    new_operation_config: dict | None = None,  # Add config parameter
) -> list[SimpleOperation | TransitionOperation | DeelTransferOperation | NewOperationType]:
    # ... existing code ...
    
    # In the unprocessed operations loop:
    for raw_operation, account_number in all_raw_operations:
        if id(raw_operation) not in processed_operations:
            # Check for new operation type (add BEFORE Deel check for priority)
            if _is_new_operation_type(raw_operation, new_operation_config):
                new_op = NewOperationType.from_raw(raw_operation)
                operations.append(new_op)
            # Check Deel transfer
            elif deel_config and _is_deel_transfer(raw_operation, deel_config):
                deel_op = DeelTransferOperation.from_raw(raw_operation)
                operations.append(deel_op)
            else:
                simple_op = SimpleOperation.from_raw(raw_operation)
                operations.append(simple_op)
    
    return operations
```

### Step 4: Add ZenMoney Transaction Mapping

**File:** `src/services/zen_money/preparer.py`

Add conversion function:

```python
def _create_new_operation_transaction(
    operation: NewOperationType, 
    timestamp: int
) -> Transaction:
    """Convert NewOperationType to ZenMoney Transaction"""
    from envs import USER_ID, CURRENCY_CONFIG
    from uuid import uuid4
    
    # Get currency configuration
    currency_cfg = CURRENCY_CONFIG.get(operation.currency, {})
    instrument_id = currency_cfg.get("instrument_id")
    account_id = currency_cfg.get("account_id")
    
    # Determine income/outcome based on your business logic
    # Example: always an expense
    income = 0
    outcome = abs(operation.field2)
    income_account = currency_cfg.get("cash_account_id")
    outcome_account = account_id
    
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
        payee=operation.field1,
        comment=f"Custom operation: {operation.field1}",
        tag=None,  # Add category logic if needed
    )
```

Update `prepare_new_state()`:

```python
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
        elif isinstance(operation, NewOperationType):  # Add this
            transaction = _create_new_operation_transaction(operation, current_timestamp)
        
        transactions.append(transaction)
    
    # ... rest of function
```

### Step 5: Update Main Entry Point

**File:** `src/main.py`

```python
from envs import DEEL_CONFIG, NEW_OPERATION_CONFIG  # Add to imports
from services.operations.operations import NewOperationType  # Add to imports

def main():
    DAYS = 7
    
    statements = get_statements(DAYS)
    zen_money_state = get_state(DAYS)
    
    # Pass new config
    operations = prepare_operations(
        statements, 
        deel_config=DEEL_CONFIG,
        new_operation_config=NEW_OPERATION_CONFIG
    )
    
    filtered_operations = filter_operations(operations, zen_money_state)
    
    if filtered_operations:
        print(f"Найдено {len(filtered_operations)} новых операций для импорта")
        
        print("\nНовые операции:")
        for i, operation in enumerate(filtered_operations, 1):
            # Add display for new type
            if isinstance(operation, NewOperationType):
                print(f"{i}. [NEW] {operation.date} - {operation.field2} {operation.currency} - {operation.field1}")
            # ... existing display logic
        
        # ... rest of main
```

### Step 6: Add Configuration

**File:** `config.yaml`

```yaml
new_operation_config:
  enabled: true
  keywords:
    - "KEYWORD1"
    - "KEYWORD2"
  # Add any custom settings
```

**File:** `src/envs.py`

```python
# Add to exports
NEW_OPERATION_CONFIG = _config.get("new_operation_config", {})
```

---

## Modifying Email Processing

### Change Email Search Criteria

**File:** `src/services/emails_statements/getter.py`

**Current search:**
```python
messages = server.search(
    f'(FROM "RaiffeisenOnline@raiffeisenbank.rs" SINCE {since_date})'
)
```

**Add subject filter:**
```python
messages = server.search(
    f'(FROM "RaiffeisenOnline@raiffeisenbank.rs" '
    f'SUBJECT "Izvod" SINCE {since_date})'
)
```

**Search specific folder:**
```python
server.select_folder("Bank Statements")  # Instead of INBOX
```

**Multiple senders:**
```python
# IMAP doesn't support OR in search, so search separately
messages1 = server.search('(FROM "sender1@example.com")')
messages2 = server.search('(FROM "sender2@example.com")')
messages = list(set(messages1 + messages2))
```

### Change Attachment Filtering

**Current logic:**
```python
if not attachment.get("filename", "").lower().endswith(".xml"):
    continue
```

**Accept multiple formats:**
```python
allowed_extensions = [".xml", ".csv", ".pdf"]
filename = attachment.get("filename", "").lower()
if not any(filename.endswith(ext) for ext in allowed_extensions):
    continue
```

**Check file size:**
```python
payload = attachment.get("payload")
if not payload:
    continue

# Skip files larger than 5MB
if len(payload) > 5 * 1024 * 1024:
    print(f"Skipping large attachment: {attachment.get('filename')}")
    continue
```

---

## Adding New Banks

### Step 1: Update Email Filtering

**File:** `src/services/emails_statements/getter.py`

```python
def get_statements(days: int = 1, bank: str = "raiffeisen") -> list[Statement]:
    server = IMAPClient("imap.gmail.com", use_uid=True, ssl=True)
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    server.select_folder("INBOX")
    
    since_date = (date.today() - timedelta(days=days)).strftime("%d-%b-%Y")
    
    # Bank-specific search criteria
    if bank == "raiffeisen":
        search_query = f'(FROM "RaiffeisenOnline@raiffeisenbank.rs" SINCE {since_date})'
    elif bank == "unicredit":
        search_query = f'(FROM "statements@unicreditbank.rs" SINCE {since_date})'
    else:
        raise ValueError(f"Unknown bank: {bank}")
    
    messages = server.search(search_query)
    
    # ... rest of function
```

### Step 2: Create Bank-Specific Parser

**Option A: Extend Statement class**

**File:** `src/services/emails_statements/statement.py`

```python
class Statement(BaseModel):
    # ... existing fields ...
    
    @classmethod
    def from_xml(cls, xml_content: str, bank: str = "raiffeisen") -> "Statement":
        if bank == "raiffeisen":
            return cls._parse_raiffeisen_xml(xml_content)
        elif bank == "unicredit":
            return cls._parse_unicredit_xml(xml_content)
        else:
            raise ValueError(f"Unknown bank: {bank}")
    
    @classmethod
    def _parse_raiffeisen_xml(cls, xml_content: str) -> "Statement":
        # Existing parsing logic
        pass
    
    @classmethod
    def _parse_unicredit_xml(cls, xml_content: str) -> "Statement":
        # New bank parsing logic
        root = etree.fromstring(xml_content.encode())
        
        # Adapt to new XML schema
        account_number = root.find(".//AccountNumber").text
        currency = root.find(".//Currency").text
        
        operations = []
        for txn in root.findall(".//Transaction"):
            operation = RawOperation(
                customer=txn.find("Payee").text or "",
                amount=float(txn.find("Amount").text or 0),
                currency=txn.find("Ccy").text or "",
                data=txn.find("Date").text or "",
                description=txn.find("Details").text or "",
                reference=txn.find("Ref").text or ""
            )
            operations.append(operation)
        
        return cls(
            account_number=account_number,
            currency=currency,
            operations=operations
        )
```

**Option B: Separate parser module**

**File:** `src/services/emails_statements/parsers/unicredit_parser.py`

```python
from lxml import etree
from ..statement import Statement, RawOperation

def parse_unicredit_xml(xml_content: str) -> Statement:
    """Parse UniCredit bank XML format"""
    root = etree.fromstring(xml_content.encode())
    
    # Bank-specific parsing logic
    # ...
    
    return Statement(
        account_number=account_number,
        currency=currency,
        operations=operations
    )
```

### Step 3: Update Configuration

**File:** `config.yaml`

```yaml
banks:
  raiffeisen:
    email_sender: "RaiffeisenOnline@raiffeisenbank.rs"
    allowed_subjects:
      - "Izvod po dinarskom racunu broj"
      - "Izvod po deviznom racunu broj"
  
  unicredit:
    email_sender: "statements@unicreditbank.rs"
    allowed_subjects:
      - "Account Statement"
```

---

## Custom Categorization Rules

### Method 1: Update category_config in YAML

**File:** `config.yaml`

```yaml
category_config:
  # Exact match (case-insensitive substring)
  "HERMES AGENCIJA": "uuid-transport-category"
  "Poreska Uprava": "uuid-taxes-category"
  
  # Multiple merchants to same category
  "MERCATOR": "uuid-groceries-category"
  "IDEA": "uuid-groceries-category"
  "LIDL": "uuid-groceries-category"
  
  # Partial match works
  "Netflix": "uuid-entertainment-category"  # Matches "NETFLIX INC"
```

### Method 2: Add Advanced Categorization Logic

**File:** `src/services/zen_money/preparer.py`

Replace simple substring matching with advanced rules:

```python
def _determine_category(operation) -> Optional[List[str]]:
    """
    Determine category tags for operation.
    Returns list of category UUIDs or None.
    """
    from envs import CATEGORY_CONFIG
    
    customer_lower = operation.customer.lower()
    
    # Method 1: Exact merchant mapping (existing)
    for merchant, category_uuid in CATEGORY_CONFIG.items():
        if merchant.lower() in customer_lower:
            return [category_uuid]
    
    # Method 2: Amount-based rules
    if abs(operation.amount) > 1000:
        return ["uuid-large-transaction-category"]
    
    # Method 3: Keyword in description
    if hasattr(operation, 'description'):
        desc_lower = operation.description.lower()
        
        if any(word in desc_lower for word in ["food", "restaurant", "cafe"]):
            return ["uuid-food-category"]
        
        if any(word in desc_lower for word in ["fuel", "gas", "petrol"]):
            return ["uuid-transport-category"]
    
    # Method 4: Pattern matching
    import re
    if re.search(r'\b(gym|fitness|sport)\b', customer_lower):
        return ["uuid-health-category"]
    
    # Method 5: Multiple categories
    categories = []
    if "business" in customer_lower:
        categories.append("uuid-business-category")
    if operation.amount < 0:  # Expense
        categories.append("uuid-expense-category")
    
    if categories:
        return categories
    
    return None
```

Update transaction creation:

```python
def _create_simple_transaction(operation, timestamp):
    # ... existing code ...
    
    # Use new categorization function
    category_tag = _determine_category(operation)
    
    return Transaction(
        # ... other fields ...
        tag=category_tag,
    )
```

### Method 3: Machine Learning Categorization

**Create new module:** `src/services/categorization/ml_categorizer.py`

```python
from typing import Optional, List

class MLCategorizer:
    """Machine learning based transaction categorizer"""
    
    def __init__(self, model_path: Optional[str] = None):
        # Load pre-trained model
        self.model = self._load_model(model_path)
    
    def predict_category(self, operation) -> Optional[List[str]]:
        """Predict category for operation"""
        # Extract features
        features = self._extract_features(operation)
        
        # Predict
        category_id = self.model.predict(features)
        
        return [category_id] if category_id else None
    
    def _extract_features(self, operation):
        """Extract features from operation"""
        return {
            'customer': operation.customer,
            'amount': operation.amount,
            'currency': operation.currency,
            'day_of_week': self._get_day_of_week(operation.date),
            # ... more features
        }
```

---

## Adding Currency Support

### Step 1: Create ZenMoney Account

1. Open ZenMoney app/website
2. Create new account for new currency (e.g., EUR)
3. Note the account UUID (from URL or API)
4. Note the instrument ID (currency ID in ZenMoney)

### Step 2: Update Configuration

**File:** `config.yaml`

```yaml
currency_config:
  USD:
    instrument_id: 1
    account_id: "existing-usd-account-uuid"
    cash_account_id: "existing-usd-cash-uuid"
  
  RSD:
    instrument_id: 12229
    account_id: "existing-rsd-account-uuid"
    cash_account_id: "existing-rsd-cash-uuid"
  
  # Add new currency
  EUR:
    instrument_id: 2  # Check ZenMoney for EUR instrument ID
    account_id: "new-eur-account-uuid"
    cash_account_id: "new-eur-cash-uuid"
```

### Step 3: No Code Changes Required!

The system automatically handles new currencies from configuration:
- `prepare_operations()` processes any currency
- `prepare_new_state()` maps using CURRENCY_CONFIG
- Duplicate detection works with any currency

### Step 4: Test with Sample Transaction

Create test statement:

```python
# In Python shell or test file
from services.emails_statements.statement import Statement, RawOperation

test_operation = RawOperation(
    customer="Test Merchant",
    amount=50.00,
    currency="EUR",
    data="2024-01-15",
    description="Test EUR transaction",
    reference="TEST123"
)

test_statement = Statement(
    account_number="EUR12345",
    currency="EUR",
    operations=[test_operation]
)

# Process normally
from services.operations.preparer import prepare_operations
operations = prepare_operations([test_statement])

# Verify EUR mapping works
from services.zen_money.preparer import prepare_new_state
state = prepare_new_state(operations)
print(state.transaction[0].incomeInstrument)  # Should be 2 (EUR)
```

---

## Debugging Common Issues

### Issue: No Emails Found

**Symptoms:**
```
Новых операций для импорта не найдено
```

**Debug steps:**

1. Check IMAP connection:
```python
# Add to getter.py temporarily
print(f"Searching for emails since: {since_date}")
print(f"Found {len(messages)} messages")
```

2. Verify email credentials:
```python
# Test connection
from imapclient import IMAPClient
server = IMAPClient("imap.gmail.com", use_uid=True, ssl=True)
try:
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    print("✓ Login successful")
except Exception as e:
    print(f"✗ Login failed: {e}")
```

3. Check allowed subjects:
```python
# Add to getter.py
print(f"Email subject: {mail.subject}")
print(f"Allowed subjects: {EMAIL_ALLOWED_SUBJECTS}")
print(f"Match: {mail.subject in EMAIL_ALLOWED_SUBJECTS}")
```

4. Expand date range:
```python
# In main.py
DAYS = 30  # Instead of 7
```

### Issue: Transactions Not Creating in ZenMoney

**Symptoms:**
- Operations found and filtered
- API call succeeds
- But transactions don't appear in ZenMoney

**Debug steps:**

1. Check account UUIDs:
```python
# Add logging in preparer.py
print(f"Income account: {income_account}")
print(f"Outcome account: {outcome_account}")
print(f"Instrument: {instrument_id}")

# Verify they exist in ZenMoney
zen_state = get_state(7)
account_ids = [acc.id for acc in zen_state.account]
print(f"Valid account IDs: {account_ids}")
```

2. Check transaction structure:
```python
# Before update_state()
print(json.dumps(state.model_dump(), indent=2, default=str))
```

3. Check API response:
```python
# In zen_money_api.py update_state()
print(f"Response status: {r.status_code}")
print(f"Response body: {r.text}")
```

4. Verify timestamps:
```python
# Transactions must not be in the future
import time
current_ts = int(time.time())
transaction_ts = int(datetime.strptime(operation.date, "%Y-%m-%d").timestamp())
print(f"Current: {current_ts}, Transaction: {transaction_ts}")
assert transaction_ts <= current_ts, "Transaction in future!"
```

### Issue: Duplicate Detection Too Aggressive

**Symptoms:**
- Operations marked as duplicates incorrectly
- Same merchant but different amounts/dates

**Debug steps:**

1. Add logging to filter.py:
```python
def _is_duplicate(operation, transaction):
    date_match = operation.date == transaction.date
    amount_match = abs(operation.amount) == abs(transaction.income - transaction.outcome)
    
    payee_match = False
    if transaction.payee:
        payee_match = (
            operation.customer.lower() in transaction.payee.lower() or
            transaction.payee.lower() in operation.customer.lower()
        )
    
    # Debug logging
    if payee_match:  # Only log potential duplicates
        print(f"\nChecking duplicate:")
        print(f"  Operation: {operation.date} {operation.amount} {operation.customer}")
        print(f"  Transaction: {transaction.date} {transaction.income-transaction.outcome} {transaction.payee}")
        print(f"  Date match: {date_match}")
        print(f"  Amount match: {amount_match}")
        print(f"  Payee match: {payee_match}")
        print(f"  Is duplicate: {date_match and amount_match and payee_match}")
    
    return date_match and amount_match and payee_match
```

2. Adjust matching criteria:
```python
# Make payee matching more strict
payee_match = transaction.payee and operation.customer.lower() == transaction.payee.lower()

# Or make amount matching more lenient (for currency conversions)
amount_match = abs(abs(operation.amount) - abs(transaction.income - transaction.outcome)) < 0.01
```

### Issue: Currency Exchange Not Linking

**Symptoms:**
- Two separate transactions instead of one exchange
- "Should be linked but aren't"

**Debug steps:**

1. Check reference numbers:
```python
# Add to preparer.py
print(f"Op1: ref={op1.reference}, desc={op1.description[:50]}")
print(f"Op2: ref={op2.reference}, desc={op2.description[:50]}")
print(f"Linked: {_are_operations_linked(op1, op2)}")
```

2. Check exchange detection:
```python
print(f"Op1 is exchange: {_is_currency_exchange(op1)}")
print(f"Op2 is exchange: {_is_currency_exchange(op2)}")
```

3. Verify criteria:
```python
print(f"Different currencies: {op1.currency != op2.currency}")
print(f"Opposite signs: {(op1.amount < 0 and op2.amount > 0) or (op1.amount > 0 and op2.amount < 0)}")
```

4. Check processing order:
```python
# Ensure both operations in same batch
print(f"All operations: {len(all_raw_operations)}")
for i, (op, acc) in enumerate(all_raw_operations):
    print(f"{i}: {op.amount} {op.currency} ref={op.reference}")
```

---

## Testing Changes

### Manual Testing

**Test with limited date range:**
```python
# In main.py
DAYS = 1  # Only test yesterday's data
```

**Test specific statement:**
```python
# Create test script: test_processing.py
from services.emails_statements.statement import Statement, RawOperation
from services.operations.preparer import prepare_operations

# Create test data
test_statement = Statement(
    account_number="TEST123",
    currency="USD",
    operations=[
        RawOperation(
            customer="Test Merchant",
            amount=100.00,
            currency="USD",
            data="2024-01-15",
            description="Test transaction",
            reference="REF123"
        )
    ]
)

# Test processing
operations = prepare_operations([test_statement])
print(f"Created {len(operations)} operations")
for op in operations:
    print(f"  - {type(op).__name__}: {op}")
```

### Unit Testing

**Create:** `tests/test_operations.py`

```python
import pytest
from services.operations.preparer import _are_operations_linked, _is_currency_exchange
from services.emails_statements.statement import RawOperation

def test_operations_linked_by_reference():
    op1 = RawOperation(
        customer="Customer1",
        amount=-100,
        currency="USD",
        data="2024-01-15",
        description="Payment",
        reference="REF123"
    )
    op2 = RawOperation(
        customer="Customer2",
        amount=100,
        currency="RSD",
        data="2024-01-15",
        description="Payment",
        reference="REF123"
    )
    
    assert _are_operations_linked(op1, op2) == True

def test_currency_exchange_detection():
    op = RawOperation(
        customer="Raiffeisen Banka",
        amount=-100,
        currency="USD",
        data="2024-01-15",
        description="Kupoprodaja deviza",
        reference="REF123"
    )
    
    assert _is_currency_exchange(op) == True

# Run with: pytest tests/
```

### Integration Testing

**Create:** `tests/test_integration.py`

```python
import pytest
from unittest.mock import Mock, patch
from services.operations.preparer import prepare_operations
from services.zen_money.preparer import prepare_new_state

def test_end_to_end_simple_operation(sample_statement):
    """Test full pipeline for simple operation"""
    
    # Process
    operations = prepare_operations([sample_statement])
    assert len(operations) == 1
    
    # Convert to ZenMoney
    state = prepare_new_state(operations)
    assert len(state.transaction) == 1
    
    # Verify transaction structure
    txn = state.transaction[0]
    assert txn.payee is not None
    assert txn.income > 0 or txn.outcome > 0

@pytest.fixture
def sample_statement():
    from services.emails_statements.statement import Statement, RawOperation
    return Statement(
        account_number="TEST123",
        currency="USD",
        operations=[
            RawOperation(
                customer="Test Merchant",
                amount=100.00,
                currency="USD",
                data="2024-01-15",
                description="Test",
                reference=""
            )
        ]
    )
```

---

## Configuration Management

### Environment-Specific Configs

**Development:** `config.dev.yaml`
```yaml
email:
  username: "dev-email@gmail.com"
  # ... dev settings

zen_money:
  api_key: "dev-api-key"
  # ... dev settings
```

**Production:** `config.prod.yaml`
```yaml
email:
  username: "prod-email@gmail.com"
  # ... prod settings

zen_money:
  api_key: "prod-api-key"
  # ... prod settings
```

**Load specific config:**
```python
# In config.py or at startup
import os

config_file = os.getenv("CONFIG_FILE", "config.yaml")
config = Config(config_file)
```

**Run with:**
```bash
CONFIG_FILE=config.dev.yaml python src/main.py
```

### Secret Management

**Using environment variables:**

```python
# In config.py
import os

class Config:
    def __init__(self, config_path: str | None = None):
        self._config = self._load_yaml(config_path)
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """Override config with environment variables"""
        if os.getenv("EMAIL_PASSWORD"):
            self._config["email"]["password"] = os.getenv("EMAIL_PASSWORD")
        
        if os.getenv("ZEN_MONEY_API_KEY"):
            self._config["zen_money"]["api_key"] = os.getenv("ZEN_MONEY_API_KEY")
```

**Using with Docker:**
```bash
docker run \
  -e EMAIL_PASSWORD=secret123 \
  -e ZEN_MONEY_API_KEY=api-key-123 \
  raiffeisen-to-zenmoney
```

---

## API Integration

### Testing API Connectivity

```python
# test_api.py
from services.zen_money.zen_money_api import get_state
from envs import ZEN_MONEY_API_KEY

def test_api_connection():
    """Test ZenMoney API connection"""
    try:
        state = get_state(1)
        print(f"✓ API connection successful")
        print(f"  Accounts: {len(state.account)}")
        print(f"  Transactions: {len(state.transaction)}")
        print(f"  Instruments: {len(state.instrument)}")
        return True
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

if __name__ == "__main__":
    test_api_connection()
```

### Handling API Rate Limits

```python
# In zen_money_api.py
import time

def update_state_with_retry(state: NewZenMoneyState, max_retries=3):
    """Update state with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return update_state(state)
        except Exception as e:
            if "429" in str(e):  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception("Max retries exceeded")
```

### Debugging API Responses

```python
# Add to zen_money_api.py
import json

def update_state(state: NewZenMoneyState):
    data = state.model_dump()
    
    # Log request
    print("=== API Request ===")
    print(json.dumps(data, indent=2, default=str))
    
    r = requests.post(
        "https://api.zenmoney.ru/v8/diff/",
        headers={"Authorization": f"Bearer {ZEN_MONEY_API_KEY}"},
        json=data,
    )
    
    # Log response
    print("=== API Response ===")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    
    if r.status_code != 200:
        raise Exception(f"Error updating state: {r.status_code} {r.text}")
    
    return r.json()
```

---

## Best Practices

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused and small

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-transaction-type

# Make changes
# ...

# Commit with descriptive message
git add .
git commit -m "feat: add support for X transaction type

- Add XOperation model
- Add detection logic
- Add ZenMoney mapping
- Update tests"

# Push and create PR
git push origin feature/new-transaction-type
```

### Configuration

- Never commit `config.yaml`
- Update `config.sample.yaml` when adding new fields
- Document all configuration options
- Use sensible defaults

### Testing

- Test with small date ranges first
- Verify in ZenMoney before expanding
- Keep test data in separate branch
- Document test scenarios

---

**End of Development Guide**