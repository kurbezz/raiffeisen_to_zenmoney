# AI Agent Documentation

This directory contains optimized documentation for AI agents working with the Raiffeisen to ZenMoney project.

## 📋 Quick Navigation

- **[QUICKSTART.md](QUICKSTART.md)** - ⚡ Start here - fast reference index
- **[NAVIGATION.md](NAVIGATION.md)** - 📍 Visual documentation map & reading paths
- **[project-metadata.yaml](project-metadata.yaml)** - Structured project metadata (YAML format)
- **[project-map.md](project-map.md)** - Complete architecture and module overview
- **[codebase-context.md](codebase-context.md)** - Detailed implementation context
- **[development-guide.md](development-guide.md)** - Development workflows and patterns
- **[VERSION.md](VERSION.md)** - Changelog & version information

## 🎯 Purpose

This documentation is optimized for:
- **Token efficiency** - Concise, structured information
- **Fast context loading** - Essential info first, details on demand
- **Accurate code generation** - Clear patterns and examples
- **Debugging assistance** - Common issues and solutions

## 🚀 Quick Start for AI Agents

### 1. Understanding the Project (Start Here)

**Fast Track (5 minutes):**
1. `QUICKSTART.md` - Quick reference & navigation
2. `project-metadata.yaml` - Project overview (50 tokens)

**Complete Understanding (15-30 minutes):**
1. `QUICKSTART.md` - Quick reference
2. `project-metadata.yaml` - Core facts
3. `project-map.md` - Architecture (300 tokens)
4. `codebase-context.md` - Implementation details (as needed)

**Not sure where to start?**
→ Read `NAVIGATION.md` for visual guide and reading strategies

### 2. Common Tasks

**Adding a new transaction type:**
- See `development-guide.md` → "Adding Transaction Types"
- Reference `codebase-context.md` → "Operations Module"

**Modifying API integration:**
- See `codebase-context.md` → "ZenMoney API Module"
- Check `project-map.md` → "Data Flow"

**Email parsing changes:**
- See `codebase-context.md` → "Email Statements Module"
- Reference XML schema in examples

## 📊 Project Overview

**Type:** Email-to-API automation tool  
**Language:** Python 3.13+  
**Architecture:** Pipeline pattern (Email → Parse → Process → Sync)  
**Key Libraries:** imapclient, lxml, pydantic, requests

## 🏗️ Architecture Summary

```
Email (IMAP)
    ↓
XML Parser (lxml)
    ↓
Operations Processor (categorization, linking)
    ↓
Duplicate Filter (date/amount matching)
    ↓
ZenMoney API (sync transactions)
```

## 📁 Module Structure

```
src/
├── config.py              # YAML configuration loader
├── envs.py                # Legacy config bridge
├── main.py                # Application entry point
└── services/
    ├── emails_statements/ # Email fetching & XML parsing
    ├── operations/        # Transaction processing & categorization
    └── zen_money/         # API integration
```

## 🔑 Key Concepts

### Transaction Types

1. **SimpleOperation** - Regular income/expense
2. **TransitionOperation** - Currency exchange (linked operations)
3. **DeelTransferOperation** - Incoming transfers from Deel

### Data Flow

1. Fetch emails with XML attachments
2. Parse XML → RawOperation objects
3. Link related operations (exchanges)
4. Categorize by merchant/keywords
5. Filter duplicates vs existing ZenMoney data
6. Create new transactions via API

## 🎨 Code Patterns

### Configuration Access
```python
from config import get_config
config = get_config()
value = config.get("path.to.value", default)
```

### Adding New Operation Type
```python
@dataclass
class NewOperation:
    field: type
    
    @classmethod
    def from_raw(cls, raw: RawOperation) -> Self:
        return cls(field=raw.field)
```

### API Models (Pydantic)
```python
class ZenMoneyModel(BaseModel):
    field: type
    optional_field: Optional[type] = None
```

## ⚠️ Important Notes

### Configuration
- Config in `config.yaml` (NEVER commit)
- Use `config.sample.yaml` as template
- Access via `config.py` module

### API Limits
- ZenMoney API: rate limits apply
- Use date ranges to limit data fetched

### Data Validation
- All models use Pydantic for validation
- XML parsing is strict (will fail on schema changes)

### Duplicate Detection
Transactions match if:
- Same date
- Same amount (absolute value)
- Same payee/customer

## 🐛 Common Issues

### Email Not Fetching
- Check `EMAIL_ALLOWED_SUBJECTS` in config
- Verify IMAP enabled in Gmail
- Use app-specific password

### Transactions Not Importing
- Verify account UUIDs in `currency_config`
- Check instrument IDs match ZenMoney
- Review duplicate filter logic

### Wrong Categorization
- Update `category_config` merchant mappings
- Check case-insensitive substring matching
- Verify category UUIDs from ZenMoney

## 📝 File Purposes

| File | Purpose | When to Modify |
|------|---------|----------------|
| `project-metadata.yaml` | Project facts | Tech stack changes |
| `project-map.md` | Architecture overview | Major refactoring |
| `codebase-context.md` | Implementation details | Feature additions |
| `development-guide.md` | How-to guides | New workflows |

## 🔍 Finding Information

**"How do I..."**
→ Check `development-guide.md`

**"What does X module do?"**
→ Check `project-map.md` then `codebase-context.md`

**"What libraries are used?"**
→ Check `project-metadata.yaml`

**"How is data structured?"**
→ Check `codebase-context.md` → Data Models

## 💡 Best Practices for AI Agents

1. **Read metadata first** - Get context before diving into code
2. **Use examples** - Reference existing patterns
3. **Validate assumptions** - Check actual code when uncertain
4. **Consider dependencies** - Changes may affect multiple modules
5. **Respect data flow** - Follow the pipeline pattern
6. **Test incrementally** - Small changes, verify often

## 🔄 Update Protocol

When the codebase changes significantly:

1. Update `project-metadata.yaml` (facts, dependencies)
2. Update `project-map.md` (architecture, modules)
3. Update `codebase-context.md` (implementation details)
4. Update `development-guide.md` (new workflows)

## 📞 Support

For human developers:
- See main `README.md` in project root
- Configuration: `config.sample.yaml`
- Troubleshooting: main README troubleshooting section

---

**Version:** 1.0  
**Last Updated:** 2024  
**Maintained for:** Claude, GPT, and other AI coding assistants