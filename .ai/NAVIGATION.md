# AI Documentation Navigation Map

**Visual guide to `.ai/` documentation structure**

---

## 📊 Documentation Tree

```
.ai/
├── README.md                    # 🏠 Master guide for AI agents
├── QUICKSTART.md                # ⚡ Start here - fast reference
├── NAVIGATION.md                # 📍 This file - visual map
├── VERSION.md                   # 📋 Changelog & version info
│
├── project-metadata.yaml        # 📦 Structured facts (YAML)
│
├── project-map.md               # 🗺️  Architecture overview
│   ├── Project Overview
│   ├── Architecture Diagrams
│   ├── Data Flow
│   ├── Module Breakdown
│   ├── Data Models
│   ├── Key Algorithms
│   ├── Configuration
│   ├── API Integration
│   └── Extension Points
│
├── codebase-context.md          # 🔍 Implementation details
│   ├── Module Deep Dive
│   ├── Code Examples
│   ├── Data Structures
│   ├── Business Logic
│   ├── Integration Details
│   ├── Common Patterns
│   └── Testing Considerations
│
└── development-guide.md         # 🛠️  How-to guides
    ├── Getting Started
    ├── Adding Transaction Types
    ├── Modifying Email Processing
    ├── Adding New Banks
    ├── Custom Categorization
    ├── Adding Currency Support
    ├── Debugging Common Issues
    ├── Testing Changes
    ├── Configuration Management
    └── API Integration
```

---

## 🎯 Quick Navigation by Role

### First-Time AI Agent

```
1. QUICKSTART.md         (2 min)  - Overview & navigation
2. project-metadata.yaml (3 min)  - Core facts
3. project-map.md        (10 min) - Architecture understanding
```

### Implementing a Feature

```
1. QUICKSTART.md         → Find relevant section
2. project-map.md        → Understand module architecture
3. codebase-context.md   → Study implementation patterns
4. development-guide.md  → Follow step-by-step guide
```

### Debugging an Issue

```
1. QUICKSTART.md         → Quick debug checklist
2. development-guide.md  → "Debugging Common Issues"
3. codebase-context.md   → Module-specific details
4. project-map.md        → Understand data flow
```

### Understanding the Codebase

```
1. project-metadata.yaml → Tech stack & dependencies
2. project-map.md        → Complete architecture
3. codebase-context.md   → Implementation details
4. development-guide.md  → Workflows & patterns
```

---

## 📖 File Purpose Quick Reference

| File | Primary Purpose | Read When |
|------|----------------|-----------|
| **README.md** | AI agent orientation | First visit |
| **QUICKSTART.md** | Fast facts & index | Every session start |
| **NAVIGATION.md** | Visual guide (this) | Need direction |
| **VERSION.md** | Track changes | Checking updates |
| **project-metadata.yaml** | Structured data | Need quick facts |
| **project-map.md** | Architecture | Understanding system |
| **codebase-context.md** | Implementation | Writing code |
| **development-guide.md** | Step-by-step tasks | Doing work |

---

## 🔍 Find Information By Topic

### Architecture & Design

→ **project-map.md**
- System architecture
- Data flow diagrams
- Module relationships
- Design patterns

### Implementation Details

→ **codebase-context.md**
- Code structure
- Function signatures
- Class definitions
- Algorithm implementations

### How-To Guides

→ **development-guide.md**
- Adding features
- Modifying behavior
- Configuration changes
- Testing procedures

### Quick Facts

→ **project-metadata.yaml**
- Dependencies
- Tech stack
- Module list
- Configuration structure

---

## 🎨 Reading Strategies

### Strategy 1: Breadth-First (Recommended)

```
QUICKSTART.md → project-metadata.yaml → project-map.md
     ↓
codebase-context.md (as needed) → development-guide.md (for tasks)
```

**Best for:** General understanding, new agents

### Strategy 2: Depth-First

```
project-map.md → codebase-context.md (specific module)
     ↓
development-guide.md (specific task)
```

**Best for:** Focused tasks, experienced agents

### Strategy 3: Task-Oriented

```
QUICKSTART.md (find task) → development-guide.md (how-to)
     ↓
codebase-context.md (details) → project-map.md (context)
```

**Best for:** Specific tasks, time-sensitive work

---

## 📏 File Size Reference

| File | Lines | Size | Read Time |
|------|-------|------|-----------|
| README.md | 210 | ~6KB | 3 min |
| QUICKSTART.md | 213 | ~6KB | 2 min |
| NAVIGATION.md | ~100 | ~3KB | 2 min |
| VERSION.md | 224 | ~6KB | 3 min |
| project-metadata.yaml | 225 | ~6KB | 3 min |
| project-map.md | 784 | ~20KB | 10-15 min |
| codebase-context.md | 1197 | ~30KB | 20-30 min |
| development-guide.md | 1199 | ~30KB | As needed |
| **TOTAL** | ~4000 | ~104KB | ~60-90 min |

**Token Estimate:** ~25,000 tokens (all files)

---

## 🚀 Recommended Reading Paths

### Path 1: Quick Onboarding (15 min)

```
1. QUICKSTART.md                  (2 min)
2. project-metadata.yaml          (3 min)
3. project-map.md - first 50%     (10 min)
```

**Result:** Understand what, why, and how the project works

### Path 2: Deep Understanding (60 min)

```
1. QUICKSTART.md                  (2 min)
2. project-metadata.yaml          (3 min)
3. project-map.md                 (15 min)
4. codebase-context.md            (30 min)
5. development-guide.md - skim    (10 min)
```

**Result:** Complete understanding, ready to code

### Path 3: Specific Task (10 min)

```
1. QUICKSTART.md - find task      (2 min)
2. development-guide.md - task    (5 min)
3. codebase-context.md - module   (3 min)
```

**Result:** Can implement specific feature/fix

---

## 🔗 Cross-Reference Index

### By Module

**config.py**
- project-map.md → "Configuration Module"
- codebase-context.md → "Configuration Module"
- development-guide.md → "Configuration Management"

**emails_statements/**
- project-map.md → "Email Statements Module"
- codebase-context.md → "Email Statements Module"
- development-guide.md → "Modifying Email Processing"

**operations/**
- project-map.md → "Operations Module"
- codebase-context.md → "Operations Module"
- development-guide.md → "Adding Transaction Types"

**zen_money/**
- project-map.md → "ZenMoney Module"
- codebase-context.md → "ZenMoney Module"
- development-guide.md → "API Integration"

### By Concept

**Transaction Types**
- project-metadata.yaml → `transaction_types`
- project-map.md → "Data Models"
- codebase-context.md → "Operations Module"
- development-guide.md → "Adding Transaction Types"

**Configuration**
- project-metadata.yaml → `configuration`
- project-map.md → "Configuration"
- codebase-context.md → "Configuration Module"
- development-guide.md → "Configuration Management"

**Data Flow**
- project-map.md → "Data Flow"
- codebase-context.md → "Business Logic"
- development-guide.md → "Debugging Common Issues"

---

## 💡 Pro Tips

1. **Start with QUICKSTART.md** - Always
2. **Use search** - All files have detailed TOC
3. **Follow links** - Extensive cross-referencing
4. **Read examples** - Every pattern has code
5. **Check VERSION.md** - For recent changes

---

## 🎓 Learning Objectives

After reading documentation:

**✓ You should understand:**
- Project purpose and architecture
- Data flow from email to API
- All module responsibilities
- Key algorithms and patterns
- Configuration structure

**✓ You should be able to:**
- Add new transaction types
- Modify categorization logic
- Debug common issues
- Add currency support
- Extend functionality

**✓ You should know where to find:**
- Code examples for patterns
- Step-by-step guides
- API documentation
- Configuration options
- Troubleshooting help

---

**Version:** 1.0  
**Last Updated:** 2024  
**Maintained for:** AI Coding Assistants