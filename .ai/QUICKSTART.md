# AI Agent Quick Reference

**Start here for fastest context loading** ⚡

---

## 🎯 What This Project Does

Syncs Raiffeisen Bank transactions from email → ZenMoney automatically.

**Pipeline:** Email (IMAP) → XML Parser → Operations Processor → ZenMoney API

---

## 📚 Documentation Files

| File | Size | When to Read |
|------|------|-------------|
| **project-metadata.yaml** | ~3KB | First - structured facts |
| **QUICKSTART.md** (this) | ~2KB | Navigation & quick ref |
| **project-map.md** | ~12KB | Architecture overview |
| **codebase-context.md** | ~20KB | Implementation details |
| **development-guide.md** | ~18KB | How-to guides |

---

## 🚀 Quick Facts

**Language:** Python 3.13+  
**Entry Point:** `src/main.py`  
**Config:** `config.yaml` (YAML format)  
**Package Manager:** uv

**Key Dependencies:**
- `imapclient` - Email fetching
- `lxml` - XML parsing
- `pydantic` - Data validation
- `requests` - API calls

---

## 📁 Project Structure (Critical Paths)

```
src/
├── main.py                    # START HERE - orchestration
├── config.py                  # Configuration loader
├── envs.py                    # Legacy config bridge
└── services/
    ├── emails_statements/     # Email & XML processing
    │   ├── getter.py          # IMAP client
    │   └── statement.py       # XML parser
    ├── operations/            # Transaction processing
    │   ├── operations.py      # Data models
    │   ├── preparer.py        # Linking & categorization
    │   └── filter.py          # Duplicate detection
    └── zen_money/             # API integration
        ├── zen_money_api.py   # API client
        └── preparer.py        # State preparation
```

---

## 🔑 Key Concepts (Must Know)

### Transaction Types

1. **SimpleOperation** - Regular income/expense
2. **TransitionOperation** - Currency exchange (2 linked operations)
3. **DeelTransferOperation** - Deel platform transfers

### Data Flow

```
Email → Statement → RawOperation → Operation → Transaction → ZenMoney
```

### Configuration Structure

```yaml
email:                    # IMAP settings
zen_money:                # API credentials
currency_config:          # Account mappings
category_config:          # Merchant → category
deel_config:              # Deel detection
```

---

## 💡 Common Tasks → Where to Look

| Task | Primary File | Reference Doc |
|------|-------------|---------------|
| Add transaction type | `operations/operations.py` | development-guide.md → "Adding Transaction Types" |
| Change email logic | `emails_statements/getter.py` | development-guide.md → "Modifying Email Processing" |
| Modify categorization | `zen_money/preparer.py` | development-guide.md → "Custom Categorization" |
| Add currency | `config.yaml` | development-guide.md → "Adding Currency Support" |
| Debug duplicates | `operations/filter.py` | development-guide.md → "Debugging Common Issues" |
| API integration | `zen_money/zen_money_api.py` | codebase-context.md → "ZenMoney Module" |

---

## 🐛 Quick Debug Checklist

**No emails found?**
→ Check `EMAIL_ALLOWED_SUBJECTS` in config.yaml

**Transactions not importing?**
→ Verify account UUIDs in `currency_config`

**Wrong categorization?**
→ Update `category_config` mappings

**Duplicates detected wrongly?**
→ Check filter logic in `operations/filter.py`

**API errors?**
→ Verify API key and user ID in config

---

## 📖 Reading Order for New Agents

**Quick Start (5 min):**
1. This file (QUICKSTART.md)
2. project-metadata.yaml

**Understanding Architecture (15 min):**
3. project-map.md → "Architecture" section
4. project-map.md → "Data Flow" section

**Implementation Details (as needed):**
5. codebase-context.md → specific module
6. development-guide.md → specific task

---

## 🔍 Search Strategy

**Looking for how something works?**
→ project-map.md first, then codebase-context.md

**Looking for how to change something?**
→ development-guide.md

**Looking for project facts?**
→ project-metadata.yaml

**Looking for specific code?**
→ Use file paths from this guide

---

## ⚡ Speed Tips

1. **Read metadata YAML first** - fastest context load
2. **Use table of contents** - all docs have them
3. **Code examples** - every guide has copy-paste ready examples
4. **Search by module name** - docs organized by module
5. **Check "Common Tasks"** - likely already documented

---

## 🎨 Code Patterns (Copy-Paste Ready)

**Config access:**
```python
from config import get_config
config = get_config()
value = config.get("path.to.key", default)
```

**New operation type:**
```python
@dataclass
class MyOperation:
    field: type
    
    @classmethod
    def from_raw(cls, raw: RawOperation) -> Self:
        return cls(field=raw.field)
```

**Pydantic model:**
```python
class MyModel(BaseModel):
    field: str
    optional: Optional[str] = None
```

---

## 🚨 Critical Warnings

1. **NEVER commit `config.yaml`** - contains secrets
2. **Use `config.sample.yaml`** - for templates
3. **Gmail needs app-specific password** - not regular password
4. **Account UUIDs must exist in ZenMoney** - check first
5. **Test with 1 day range first** - avoid bulk mistakes

---

## 📞 Need More Detail?

**Architecture questions** → project-map.md  
**Implementation questions** → codebase-context.md  
**How-to questions** → development-guide.md  
**Configuration questions** → config.sample.yaml + development-guide.md

---

**Version:** 1.0  
**Last Updated:** 2024  
**Optimized for:** Claude, GPT-4, and other AI coding assistants