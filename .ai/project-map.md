# Project Map: Raiffeisen to ZenMoney

**Version:** 1.0  
**Purpose:** Comprehensive architecture and module overview for AI agents

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Module Breakdown](#module-breakdown)
5. [Data Models](#data-models)
6. [Key Algorithms](#key-algorithms)
7. [Configuration](#configuration)
8. [API Integration](#api-integration)
9. [Error Handling](#error-handling)
10. [Extension Points](#extension-points)

---

## Project Overview

### Purpose
Automates synchronization of Raiffeisen Bank Serbia transactions from email statements to ZenMoney financial tracking service.

### Key Features
- Fetches bank statement emails via IMAP
- Parses XML transaction data
- Links related operations (currency exchanges)
- Categorizes transactions automatically
- Detects and handles Deel transfers
- Prevents duplicate imports
- Syncs to ZenMoney API

### Technology Stack
- **Language:** Python 3.13+
- **Email:** imapclient (IMAP protocol)
- **Parsing:** lxml (XML), mail-parser (email)
- **Validation:** Pydantic v2
- **HTTP:** requests
- **Config:** PyYAML

---

## Architecture

### Pattern
**Pipeline Architecture** - Sequential data transformation stages

```
┌─────────────────┐
│  Email Source   │ Gmail IMAP
│  (IMAP Client)  │
└────────┬────────┘
         │ XML Attachments
         ▼
┌─────────────────┐
│  XML Parser     │ lxml
│  (Statement)    │
└────────┬────────┘
         │ RawOperation[]
         ▼
┌─────────────────┐
│  Operations     │ Link & Categorize
│  Processor      │
└────────┬────────┘
         │ SimpleOperation | TransitionOperation | DeelTransferOperation
         ▼
┌─────────────────┐
│  Duplicate      │ Compare with ZenMoney
│  Filter         │
└────────┬────────┘
         │ Filtered Operations
         ▼
┌─────────────────┐
│  ZenMoney       │ Prepare API Payload
│  Preparer       │
└────────┬────────┘
         │ NewZenMoneyState
         ▼
┌─────────────────┐
│  ZenMoney API   │ POST /v8/diff/
│  Client         │
└─────────────────┘
```

### Directory Structure

```
raiffeisen_to_zenmoney/
├── .ai/                          # AI agent documentation
│   ├── README.md                 # This guide
│   ├── project-metadata.yaml    # Structured metadata
│   ├── project-map.md           # Architecture overview
│   ├── codebase-context.md      # Implementation details
│   └── development-guide.md     # How-to guides
│
├── src/
│   ├── config.py                # Configuration loader
│   ├── envs.py                  # Legacy config bridge
│   ├── main.py                  # Entry point
│   │
│   └── services/
│       ├── emails_statements/   # Email & XML processing
│       │   ├── getter.py        # IMAP client
│       │   └── statement.py     # XML parser & models
│       │
│       ├── operations/          # Transaction processing
│       │   ├── operations.py    # Data models
│       │   ├── preparer.py      # Linking & categorization
│       │   └── filter.py        # Duplicate detection
│       │
│       └── zen_money/           # API integration
│           ├── zen_money_api.py # API client & models
│           └── preparer.py      # State preparation
│
├── config.yaml                  # Runtime configuration (not committed)
├── config.sample.yaml           # Configuration template
├── pyproject.toml               # Project metadata
├── Dockerfile                   # Container definition
└── README.md                    # User documentation
```

---

## Data Flow

### Step-by-Step Process

```
1. FETCH EMAILS (emails_statements/getter.py)
   ├─ Connect to Gmail via IMAP
   ├─ Search for Raiffeisen emails in last N days
   ├─ Filter by allowed subjects
   └─ Extract XML attachments
   
2. PARSE XML (emails_statements/statement.py)
   ├─ Decode base64 attachment
   ├─ Parse XML with lxml
   ├─ Extract account number, currency
   ├─ Parse each operation (amount, date, customer, etc.)
   └─ Return Statement objects
   
3. PROCESS OPERATIONS (operations/preparer.py)
   ├─ Collect all RawOperations from all statements
   ├─ Link related operations:
   │  ├─ Match by reference number
   │  ├─ Match by description
   │  └─ Create TransitionOperation for exchanges
   ├─ Detect Deel transfers (keyword matching)
   └─ Create SimpleOperation for unlinked operations
   
4. FILTER DUPLICATES (operations/filter.py)
   ├─ Fetch existing ZenMoney transactions
   ├─ For each new operation:
   │  ├─ Compare date
   │  ├─ Compare amount (absolute value)
   │  └─ Compare payee/customer
   └─ Return only new operations
   
5. PREPARE API PAYLOAD (zen_money/preparer.py)
   ├─ Convert operations to Transaction objects
   ├─ Set income/outcome based on amount sign
   ├─ Map currencies to instrument IDs
   ├─ Map accounts to account UUIDs
   ├─ Apply category mappings
   └─ Build NewZenMoneyState
   
6. SYNC TO API (zen_money/zen_money_api.py)
   ├─ POST to ZenMoney API
   ├─ Include server timestamp
   ├─ Send transaction array
   └─ Handle response/errors
```

### Data Transformations

```
Email (RFC822)
    ↓
Mail Object (mailparser)
    ↓
XML String (base64 decoded)
    ↓
Statement (Pydantic model)
    ├─ account_number: str
    ├─ currency: str
    └─ operations: RawOperation[]
        ├─ customer: str
        ├─ amount: float
        ├─ currency: str
        ├─ date: str
        ├─ description: str
        └─ reference: str
    ↓
Operations (typed)
    ├─ SimpleOperation
    ├─ TransitionOperation
    └─ DeelTransferOperation
    ↓
Filtered Operations (no duplicates)
    ↓
Transaction[] (ZenMoney format)
    ├─ id: UUID
    ├─ date: str
    ├─ income: float
    ├─ outcome: float
    ├─ incomeAccount: UUID
    ├─ outcomeAccount: UUID
    └─ ...
    ↓
NewZenMoneyState
    └─ POST to API
```

---

## Module Breakdown

### 1. Configuration Module (`config.py`)

**Purpose:** Load and provide access to YAML configuration

**Key Classes:**
- `Config` - Configuration manager

**Key Functions:**
- `get_config()` - Singleton config instance
- `get(key, default)` - Get nested config values

**Properties:**
- `email_username`, `email_password`, `email_allowed_subjects`
- `zen_money_api_key`, `zen_money_user_id`
- `currency_config`, `category_config`, `deel_config`

**Usage:**
```python
from config import get_config
config = get_config()
api_key = config.zen_money_api_key
```

---

### 2. Environment Bridge (`envs.py`)

**Purpose:** Legacy compatibility layer for environment-based config access

**Exports:**
- `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `EMAIL_ALLOWED_SUBJECTS`
- `ZEN_MONEY_API_KEY`, `USER_ID`
- `CURRENCY_CONFIG`, `CATEGORY_CONFIG`, `DEEL_CONFIG`

**Implementation:** Loads from `config.py` and exposes as module constants

---

### 3. Main Entry Point (`main.py`)

**Purpose:** Orchestrate the entire pipeline

**Function:** `main()`

**Process:**
1. Set time range (default: 7 days)
2. Fetch statements from email
3. Fetch current ZenMoney state
4. Prepare operations
5. Filter duplicates
6. Display summary
7. Sync to ZenMoney
8. Report results

**Error Handling:** Exceptions propagate to top level

---

### 4. Email Statements Module (`services/emails_statements/`)

#### 4.1. Getter (`getter.py`)

**Purpose:** Fetch bank statements from email

**Key Function:** `get_statements(days: int) -> list[Statement]`

**Process:**
1. Connect to Gmail IMAP (imap.gmail.com)
2. Login with credentials
3. Search inbox for Raiffeisen emails since N days ago
4. Filter by allowed subjects
5. Extract XML attachments
6. Parse each XML to Statement
7. Return list of statements

**Dependencies:**
- `imapclient.IMAPClient`
- `mailparser`
- `envs` (EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_ALLOWED_SUBJECTS)

#### 4.2. Statement Parser (`statement.py`)

**Purpose:** Parse XML bank statements

**Key Classes:**
- `RawOperation` - Single transaction from XML
- `Statement` - Complete bank statement

**RawOperation Fields:**
- `customer: str` - Payee/merchant name
- `amount: float` - Transaction amount (+ income, - expense)
- `currency: str` - Currency code (USD, RSD)
- `data: str` - Transaction date (YYYY-MM-DD)
- `description: str` - Full transaction description
- `reference: str` - Reference number for linking

**Statement Fields:**
- `account_number: str` - Bank account number
- `currency: str` - Account currency
- `operations: list[RawOperation]` - All transactions

**Key Method:** `Statement.from_xml(xml_content: str) -> Statement`
- Parses XML using lxml
- Extracts account info
- Parses each operation element
- Returns Statement object

---

### 5. Operations Module (`services/operations/`)

#### 5.1. Operations Models (`operations.py`)

**Purpose:** Define typed operation models

**Classes:**

**SimpleOperation:**
- Regular income/expense transaction
- Fields: `customer`, `amount`, `currency`, `date`
- Created from: Unlinked RawOperation

**TransitionOperation:**
- Currency exchange (buy/sell pair)
- Fields: `from_amount`, `from_currency`, `to_amount`, `to_currency`, `date`
- Created from: Two linked RawOperations with different currencies

**DeelTransferOperation:**
- Incoming transfer from Deel
- Fields: `customer`, `amount`, `currency`, `date`
- Created from: RawOperation matching Deel keywords

All have `@classmethod from_raw()` factory method

#### 5.2. Operations Preparer (`preparer.py`)

**Purpose:** Link operations and categorize them

**Key Function:** `prepare_operations(statements, deel_config) -> list[Operation]`

**Algorithm:**
1. Flatten all RawOperations from all statements
2. Find linked operation pairs:
   - Match by reference number
   - Match by reference in description
3. For linked pairs with different currencies:
   - Identify currency exchange operations
   - Create TransitionOperation (from negative to positive)
   - Mark both as processed
4. For remaining unprocessed operations:
   - Check if Deel transfer (if enabled)
   - Create DeelTransferOperation or SimpleOperation
5. Return all operations

**Helper Functions:**

`_are_operations_linked(op1, op2) -> bool`
- Same reference number, OR
- Reference appears in other's description

`_is_currency_exchange(operation) -> bool`
- Contains keywords: "otkup", "kupoprodaja deviza", "protivvrednost"
- Customer is "raiffeisen banka"

`_is_deel_transfer(operation, deel_config) -> bool`
- Deel enabled in config
- Amount is positive (incoming)
- Customer/description contains Deel keywords

#### 5.3. Operations Filter (`filter.py`)

**Purpose:** Remove duplicate transactions

**Key Function:** `filter_operations(operations, zen_money_state) -> list[Operation]`

**Duplicate Detection Logic:**
- For each operation, check against existing ZenMoney transactions
- Match criteria (all must match):
  - Same date
  - Same absolute amount
  - Same payee/customer (case-insensitive contains)
- Return only non-duplicate operations

**Special Cases:**
- TransitionOperation: checks both from/to amounts
- DeelTransferOperation: checks as transfer between accounts

---

### 6. ZenMoney Module (`services/zen_money/`)

#### 6.1. API Client (`zen_money_api.py`)

**Purpose:** Interact with ZenMoney API v8

**API Endpoint:** `https://api.zenmoney.ru/v8/diff/`

**Key Models (Pydantic):**
- `Instrument` - Currency/asset definition
- `Account` - Bank account, cash, credit card, etc.
- `Transaction` - Single financial transaction
- `Budget` - Budget entries
- `Reminder` - Scheduled transactions
- `ReminderMarker` - Reminder instances
- `ZenMoneyState` - Complete state from API
- `NewZenMoneyState` - Updates to send to API

**Key Functions:**

`get_state(days: int) -> ZenMoneyState`
- Calculates timestamps (current and N days ago)
- POSTs to /v8/diff/ with timestamps
- Receives current state
- Returns parsed ZenMoneyState

`update_state(state: NewZenMoneyState) -> dict`
- Prepares state object (removes None fields)
- POSTs to /v8/diff/
- Returns API response
- Raises exception on error

**Authentication:** Bearer token in Authorization header

#### 6.2. State Preparer (`preparer.py`)

**Purpose:** Convert operations to ZenMoney transaction format

**Key Function:** `prepare_new_state(operations) -> NewZenMoneyState`

**Process:**
1. For each operation, create Transaction object:
   - Generate unique ID (UUID)
   - Set timestamps (current time)
   - Map amount to income/outcome
   - Map currency to instrument ID
   - Map to account UUIDs
   - Apply category if merchant matches
   - Set payee/comment
2. Build NewZenMoneyState with:
   - Current timestamp
   - Server timestamp (from previous fetch)
   - Transaction array

**Operation Mapping:**

**SimpleOperation → Transaction:**
- Positive amount: income to account, outcome from cash
- Negative amount: income from cash, outcome to account
- Single account involved

**TransitionOperation → Transaction:**
- Outcome from source currency account
- Income to target currency account
- opIncome/opOutcome for original amounts

**DeelTransferOperation → Transaction:**
- Transfer type
- Outcome from Deel account (config)
- Income to bank account
- Both in same currency

---

## Data Models

### Email Layer

```
Mail (mailparser)
└─ attachments[]
   └─ payload: base64 XML
```

### Statement Layer

```
Statement (Pydantic)
├─ account_number: str
├─ currency: str
└─ operations: RawOperation[]
   ├─ customer: str
   ├─ amount: float
   ├─ currency: str
   ├─ data: str (date)
   ├─ description: str
   └─ reference: str
```

### Operation Layer

```
SimpleOperation
├─ customer: str
├─ amount: float
├─ currency: str
└─ date: str

TransitionOperation
├─ from_amount: float
├─ from_currency: str
├─ to_amount: float
├─ to_currency: str
└─ date: str

DeelTransferOperation
├─ customer: str
├─ amount: float
├─ currency: str
└─ date: str
```

### ZenMoney Layer

```
Transaction (Pydantic)
├─ id: str (UUID)
├─ user: int
├─ date: str (YYYY-MM-DD)
├─ income: float
├─ outcome: float
├─ incomeInstrument: int
├─ outcomeInstrument: int
├─ incomeAccount: str (UUID)
├─ outcomeAccount: str (UUID)
├─ created: int (timestamp)
├─ changed: int (timestamp)
├─ deleted: bool
├─ viewed: bool
├─ payee: Optional[str]
├─ comment: Optional[str]
├─ tag: Optional[List[str]]
├─ opIncome: Optional[float]
├─ opOutcome: Optional[float]
└─ ... (more optional fields)
```

---

## Key Algorithms

### 1. Operation Linking

**Location:** `operations/preparer.py`

**Purpose:** Connect related transactions (e.g., currency exchange pairs)

**Logic:**
```
For each operation pair (i, j where j > i):
    If operations are linked (same reference):
        If different currencies AND opposite signs AND is currency exchange:
            Determine from_op (negative) and to_op (positive)
            Create TransitionOperation
            Mark both as processed
            Break inner loop
```

**Linking Criteria:**
- Same reference number, OR
- Reference appears in description

**Exchange Criteria:**
- Different currencies
- Opposite signs (one -, one +)
- Contains exchange keywords

### 2. Duplicate Detection

**Location:** `operations/filter.py`

**Purpose:** Prevent re-importing existing transactions

**Logic:**
```
For each new operation:
    For each existing ZenMoney transaction:
        If same_date AND same_amount AND same_payee:
            Mark as duplicate
            Break
    If not duplicate:
        Add to filtered list
```

**Matching Rules:**
- Date: exact match (YYYY-MM-DD)
- Amount: absolute value match
- Payee: case-insensitive substring match

### 3. Category Assignment

**Location:** `zen_money/preparer.py`

**Purpose:** Auto-categorize transactions by merchant

**Logic:**
```
For each operation:
    For each merchant in category_config:
        If merchant in operation.customer (case-insensitive):
            Assign category UUID
            Break
```

### 4. Deel Detection

**Location:** `operations/preparer.py`

**Purpose:** Identify incoming Deel payments

**Logic:**
```
If deel_config.enabled AND amount > 0:
    For each keyword in deel_config.keywords:
        If keyword in (customer OR description) (case-insensitive):
            Return True
Return False
```

---

## Configuration

### File Structure (`config.yaml`)

```yaml
email:
  username: "email@gmail.com"
  password: "app-password"
  allowed_subjects: ["Subject 1", "Subject 2"]

zen_money:
  api_key: "api-key"
  user_id: 123456

currency_config:
  USD:
    instrument_id: 1
    account_id: "uuid"
    cash_account_id: "uuid"
  RSD:
    instrument_id: 12229
    account_id: "uuid"
    cash_account_id: "uuid"

category_config:
  "Merchant Name": "category-uuid"

deel_config:
  enabled: true
  keywords: ["DEEL", "DEEL INC"]
  account_id: "uuid"
  currency: "USD"
```

### Configuration Access

```python
# Modern way
from config import get_config
config = get_config()
value = config.get("section.key", default)

# Legacy way (still works)
from envs import EMAIL_USERNAME
```

---

## API Integration

### ZenMoney API v8

**Endpoint:** `https://api.zenmoney.ru/v8/diff/`

**Method:** POST

**Authentication:** Bearer token

**Request Format:**
```json
{
  "currentClientTimestamp": 1234567890,
  "serverTimestamp": 1234560000,
  "transaction": [...] // optional
}
```

**Response Format:**
```json
{
  "serverTimestamp": 1234567890,
  "instrument": [...],
  "account": [...],
  "transaction": [...],
  "budget": [...],
  "reminder": [...],
  "reminderMarker": [...]
}
```

**Sync Pattern:**
1. Get current state (serverTimestamp from N days ago)
2. Process new transactions
3. Send updates (new transactions)
4. API merges changes

---

## Error Handling

### Current Approach
- Exceptions propagate to `main()`
- API errors raise exceptions with status code
- Configuration errors raise FileNotFoundError
- Validation errors from Pydantic

### Common Errors

**Email Errors:**
- IMAP connection failed → Check credentials
- No emails found → Check date range, subjects
- XML parse error → Bank changed format

**API Errors:**
- 401 Unauthorized → Check API key
- 400 Bad Request → Validate transaction format
- 500 Server Error → ZenMoney service issue

**Configuration Errors:**
- File not found → Create config.yaml
- Invalid YAML → Check syntax
- Missing required fields → Compare with sample

---

## Extension Points

### Adding New Operation Types

1. Define model in `operations/operations.py`
2. Add detection logic in `operations/preparer.py`
3. Add mapping in `zen_money/preparer.py`
4. Update filter if needed

### Adding New Banks

1. Modify `emails_statements/getter.py` (search criteria)
2. Update `statement.py` parser (XML schema)
3. Add to allowed subjects in config

### Custom Categorization

1. Add rules in `operations/preparer.py`
2. Or extend `category_config` in YAML

### Additional Currencies

1. Add to `currency_config` in YAML
2. Get instrument ID from ZenMoney
3. Create accounts in ZenMoney first

---

**End of Project Map**