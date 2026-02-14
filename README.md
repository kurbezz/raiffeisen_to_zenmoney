# Raiffeisen to ZenMoney

Automated tool to sync Raiffeisen bank transactions from email to ZenMoney financial tracking service.

## 🎯 What It Does

1. Fetches Raiffeisen bank statement emails via IMAP
2. Parses XML transaction data
3. Intelligently categorizes transactions (currency exchanges, Deel transfers, etc.)
4. Syncs new transactions to ZenMoney via API
5. Prevents duplicates automatically

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Gmail account with IMAP enabled
- ZenMoney account with API access

### Installation

```bash
# Clone repository
git clone <repository-url>
cd raiffeisen_to_zenmoney

# Install dependencies
uv sync
```

### Configuration

```bash
# Copy sample config
cp config.sample.yaml config.yaml

# Edit config.yaml with your credentials:
# - Gmail username and app-specific password
# - ZenMoney API key and user ID
# - Account UUIDs from ZenMoney
# - Category mappings (optional)
```

### Run

```bash
python src/main.py
```

The application will:
- Fetch statements from the last 7 days
- Process and categorize transactions
- Import new transactions to ZenMoney

## 📚 Documentation

All project documentation is organized in the **`.ai/`** directory for optimal AI agent usage:

### For AI Agents (Start Here) 🤖

- **[.ai/QUICKSTART.md](.ai/QUICKSTART.md)** - ⚡ Quick reference (start here)
- **[.ai/project-metadata.yaml](.ai/project-metadata.yaml)** - Structured project facts
- **[.ai/project-map.md](.ai/project-map.md)** - Complete architecture overview
- **[.ai/codebase-context.md](.ai/codebase-context.md)** - Detailed implementation context
- **[.ai/development-guide.md](.ai/development-guide.md)** - How-to guides for common tasks
- **[.ai/README.md](.ai/README.md)** - Full guide for AI assistants

### For Human Developers 👨‍💻

- **This README** - User documentation and quick start
- **[config.sample.yaml](config.sample.yaml)** - Configuration template
- **[.ai/development-guide.md](.ai/development-guide.md)** - Development workflows

## ✨ Features

- **Smart Transaction Detection**
  - Currency exchanges (linked operations)
  - Deel payment transfers
  - Regular income/expense transactions

- **Auto-Categorization**
  - Merchant name matching
  - Configurable category mappings

- **Duplicate Prevention**
  - Compares with existing ZenMoney transactions
  - Date, amount, and payee matching

- **Multi-Currency Support**
  - USD and RSD (extensible)
  - Automatic currency conversion tracking

## 🔧 Configuration

### Email Settings

```yaml
email:
  username: "your-email@gmail.com"
  password: "app-specific-password"
  allowed_subjects:
    - "Izvod po dinarskom racunu broj"
    - "Izvod po deviznom racunu broj"
```

### ZenMoney API

```yaml
zen_money:
  api_key: "your-api-key"
  user_id: 1234567
```

### Currency Accounts

```yaml
currency_config:
  USD:
    instrument_id: 1
    account_id: "uuid-from-zenmoney"
    cash_account_id: "uuid-from-zenmoney"
```

### Category Mappings

```yaml
category_config:
  "Merchant Name": "category-uuid-from-zenmoney"
```

### Deel Integration

```yaml
deel_config:
  enabled: true
  keywords: ["DEEL", "DEEL INC"]
  account_id: "deel-account-uuid"
  currency: "USD"
```

## 🏗️ Architecture

```
Email (IMAP) → XML Parser → Operations Processor → ZenMoney API
                                    ↓
                            [Simple, Exchange, Deel]
                                    ↓
                            Duplicate Filter
                                    ↓
                            Transaction Creator
```

## 🛠️ Development

```bash
# Format code
black src/

# Lint
ruff check src/

# Run tests
pytest
```

## 📦 Dependencies

- **imapclient** - Email fetching
- **lxml** - XML parsing
- **pydantic** - Data validation
- **requests** - API calls
- **pyyaml** - Configuration

## 🔒 Security

- Never commit `config.yaml` (in `.gitignore`)
- Use app-specific passwords for Gmail
- Store API keys only in config file
- No credentials in code

## 🤝 Contributing

1. Read [.ai/project-map.md](.ai/project-map.md) to understand architecture
2. Check [.ai/codebase-context.md](.ai/codebase-context.md) for implementation details
3. Follow [.ai/development-guide.md](.ai/development-guide.md) for workflows
4. Follow existing code patterns
5. Maintain type hints and documentation
6. Test with small date ranges (DAYS=1 first)

## 📝 License

[Add your license here]

## 🐛 Troubleshooting

### Email not fetching
- Check Gmail IMAP is enabled
- Verify app-specific password (not regular password)
- Test network connectivity

### Transactions not importing
- Verify ZenMoney account UUIDs in config
- Check currency instrument IDs match ZenMoney
- Review filtering logic (may be duplicates)

### Wrong categorization
- Check merchant names in `category_config`
- Verify category UUIDs from ZenMoney
- Note: matching is case-insensitive substring

### Deel transfers not detected
- Ensure `deel_config.enabled: true`
- Verify keywords match payment descriptions
- Check amount is positive (incoming)

---

**📖 Complete Documentation:** See [.ai/](.ai/) directory

**🤖 For AI Agents:** Start with [.ai/QUICKSTART.md](.ai/QUICKSTART.md)

**👨‍💻 For Developers:** See [.ai/development-guide.md](.ai/development-guide.md)