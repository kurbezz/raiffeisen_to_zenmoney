# Documentation Maintenance Guide

**For maintaining `.ai/` documentation accuracy and currency**

---

## 🎯 Purpose

This guide ensures the AI documentation stays synchronized with the codebase and remains useful for AI agents.

---

## 📋 When to Update Documentation

### Immediate Updates Required

**Code Changes:**
- ✅ New module added → Update all architecture docs
- ✅ Module removed/renamed → Update all references
- ✅ API endpoint changed → Update codebase-context.md
- ✅ Data model changed → Update project-map.md + codebase-context.md
- ✅ Configuration schema changed → Update all relevant docs

**Dependencies:**
- ✅ New dependency added → Update project-metadata.yaml
- ✅ Dependency version changed → Update project-metadata.yaml
- ✅ Dependency removed → Update project-metadata.yaml

**Architecture:**
- ✅ Data flow changed → Update project-map.md
- ✅ New pattern introduced → Update codebase-context.md
- ✅ Integration point added → Update project-map.md

### Optional Updates

**Nice to have:**
- ⚠️ Minor refactoring → Consider updating examples
- ⚠️ Performance improvements → Add notes
- ⚠️ Bug fixes → Update known issues section

---

## 🔄 Update Checklist

### For Code Changes

```
□ Identify affected documentation files
□ Update project-metadata.yaml (if tech stack changed)
□ Update project-map.md (if architecture changed)
□ Update codebase-context.md (if implementation changed)
□ Update development-guide.md (if workflow changed)
□ Update code examples (if patterns changed)
□ Verify cross-references still valid
□ Update VERSION.md changelog
□ Increment version number
```

### For New Features

```
□ Add to project-metadata.yaml → extension_points
□ Document in project-map.md → Module Breakdown
□ Add implementation details to codebase-context.md
□ Create how-to guide in development-guide.md
□ Add code examples
□ Update QUICKSTART.md if major feature
□ Update VERSION.md
```

### For Deprecations

```
□ Mark as deprecated in all docs
□ Add migration guide to development-guide.md
□ Update examples to use new approach
□ Remove from QUICKSTART.md after grace period
□ Update VERSION.md
```

---

## 📁 File-Specific Responsibilities

### README.md
**Update when:**
- Documentation structure changes
- New files added to .ai/
- Navigation changes

**Typical changes:**
- Add/remove file from navigation
- Update reading order
- Modify quick start steps

### QUICKSTART.md
**Update when:**
- Major architectural changes
- Common tasks change
- New critical patterns emerge

**Typical changes:**
- Update quick facts
- Modify common tasks table
- Add new patterns to reference

### NAVIGATION.md
**Update when:**
- New documentation files added
- File purposes change
- Reading paths need adjustment

**Typical changes:**
- Add files to tree
- Update cross-references
- Adjust reading strategies

### project-metadata.yaml
**Update when:**
- Dependencies change
- Tech stack changes
- Modules added/removed
- Configuration structure changes

**Typical changes:**
- Add/remove dependencies
- Update module list
- Modify data models list
- Change version numbers

### project-map.md
**Update when:**
- Architecture changes
- New modules added
- Data flow changes
- API integration changes

**Typical changes:**
- Update architecture diagrams
- Add new modules to breakdown
- Modify data flow descriptions
- Update module relationships

### codebase-context.md
**Update when:**
- Implementation details change
- New patterns introduced
- Code examples need updates
- Business logic changes

**Typical changes:**
- Update function signatures
- Add new code examples
- Modify algorithm descriptions
- Update integration details

### development-guide.md
**Update when:**
- Workflows change
- New common tasks emerge
- Setup process changes
- Testing procedures change

**Typical changes:**
- Add new how-to sections
- Update step-by-step guides
- Modify code examples
- Add debugging tips

### VERSION.md
**Update when:**
- ANY documentation changes
- Version increments
- New features documented

**Typical changes:**
- Add changelog entry
- Increment version
- Update coverage matrix
- Modify quality metrics

---

## 🔢 Version Numbering

**Format:** MAJOR.MINOR.PATCH

### MAJOR (1.x.x → 2.x.x)
- Complete documentation restructure
- Breaking changes in navigation
- New documentation paradigm

### MINOR (x.1.x → x.2.x)
- New documentation files
- Significant new sections
- Major feature documentation

### PATCH (x.x.1 → x.x.2)
- Small corrections
- Example updates
- Typo fixes
- Cross-reference updates

**Current:** 1.0.0

---

## ✅ Quality Checks

### Before Committing Updates

```bash
# 1. Check for broken links (manual)
grep -r "\[.*\](.*)" .ai/*.md | grep -v "http"

# 2. Verify YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.ai/project-metadata.yaml'))"

# 3. Check file sizes (should be reasonable)
ls -lh .ai/

# 4. Count lines (track growth)
wc -l .ai/*.md .ai/*.yaml
```

### Quality Criteria

**Completeness:**
- [ ] All modules documented
- [ ] All public APIs covered
- [ ] All configuration options explained
- [ ] Common tasks have guides

**Accuracy:**
- [ ] Code examples work
- [ ] File paths correct
- [ ] Cross-references valid
- [ ] Versions match reality

**Clarity:**
- [ ] Clear section headings
- [ ] Good code examples
- [ ] Concise explanations
- [ ] Proper formatting

**Discoverability:**
- [ ] Table of contents present
- [ ] Cross-references abundant
- [ ] Good navigation
- [ ] Search-friendly structure

---

## 🎨 Style Guidelines

### Writing Style

**Do:**
- ✅ Use clear, concise language
- ✅ Include working code examples
- ✅ Use tables for comparisons
- ✅ Add emoji for visual scanning
- ✅ Cross-reference related sections

**Don't:**
- ❌ Write long paragraphs
- ❌ Use jargon without explanation
- ❌ Provide broken examples
- ❌ Duplicate information
- ❌ Forget to update cross-refs

### Markdown Formatting

**Headings:**
```markdown
# H1 - File title only
## H2 - Major sections
### H3 - Subsections
#### H4 - Rare, for deep nesting
```

**Code blocks:**
```markdown
# Always specify language
```python
def example():
    pass
```

# Or use path-based format
```path/to/file.py
def example():
    pass
```
```

**Tables:**
```markdown
| Column | Column |
|--------|--------|
| Data   | Data   |
```

**Lists:**
```markdown
- Use `-` for unordered
1. Use numbers for ordered
- [ ] Use checkboxes for tasks
```

---

## 🔍 Review Process

### Self-Review Checklist

Before pushing documentation updates:

```
□ Read through all changed files
□ Verify code examples work
□ Check cross-references
□ Run quality checks (see above)
□ Update VERSION.md
□ Commit with clear message
```

### Commit Message Format

```
docs(ai): brief description

- Detailed change 1
- Detailed change 2
- Related to: issue #123

Updated files:
- .ai/file1.md
- .ai/file2.yaml
```

---

## 🚨 Common Pitfalls

### Avoid These Mistakes

1. **Forgetting to update VERSION.md**
   - Always log changes
   - Keep changelog current

2. **Breaking cross-references**
   - Check all links after renaming
   - Use find/replace carefully

3. **Outdated examples**
   - Test code examples
   - Keep patterns synchronized

4. **Inconsistent formatting**
   - Follow style guide
   - Use consistent headings

5. **Missing updates across files**
   - One change often affects multiple files
   - Use checklist above

---

## 🛠️ Tools & Scripts

### Useful Commands

**Find all TODO markers:**
```bash
grep -r "TODO" .ai/
```

**Check documentation size:**
```bash
du -sh .ai/
```

**List all cross-references:**
```bash
grep -rn "\.md\|\.yaml" .ai/ | grep "\["
```

**Count total lines:**
```bash
find .ai -name "*.md" -o -name "*.yaml" | xargs wc -l
```

### Future Automation Ideas

- [ ] Script to check broken links
- [ ] Auto-generate module list from code
- [ ] Lint documentation for style
- [ ] Auto-update version from git commits
- [ ] Validate YAML schemas

---

## 📅 Maintenance Schedule

### Regular Reviews

**After each major release:**
- Review all documentation
- Update examples
- Check accuracy
- Update version

**Monthly:**
- Check for TODOs
- Review recent issues
- Update troubleshooting
- Verify links

**Quarterly:**
- Complete documentation audit
- Update reading estimates
- Review quality metrics
- Plan improvements

---

## 🤝 Contribution Guidelines

### For Documentation Contributors

1. **Read existing docs first**
   - Understand style and structure
   - Match existing patterns

2. **Make focused changes**
   - One topic per update
   - Keep commits atomic

3. **Update related files**
   - Use checklist above
   - Don't forget cross-refs

4. **Test your changes**
   - Verify examples work
   - Check rendering

5. **Update VERSION.md**
   - Log your changes
   - Increment version

---

## 📞 Getting Help

**Questions about documentation:**
- Check VERSION.md for recent changes
- Review NAVIGATION.md for structure
- Look at existing patterns

**Unsure what to update:**
- Use update checklist above
- Check file responsibilities
- When in doubt, update all

**Technical issues:**
- Check YAML syntax
- Verify markdown rendering
- Test code examples

---

**Maintained by:** Project maintainers  
**Last updated:** 2024  
**Version:** 1.0.0