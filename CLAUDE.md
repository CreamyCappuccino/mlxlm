# 🤖 MLX-LM Development Workflow Guide

**⚠️ Note**: Claude Cloud credits are now exhausted. Development is local-only from this point forward.

This document defines the collaborative workflow between **Claude Cloud** and **Claude Local** (Claude Code) to ensure smooth development and version control.

---

## 📋 Overview

- **Claude Cloud**: Web-based Claude working on GitHub directly (dev branch)
- **Claude Local**: Claude Code in terminal (local machine, working directory)
- **Source of Truth**: `dev` branch on GitHub
- **Goal**: Avoid conflicts, maintain clear responsibilities, and keep both instances synchronized

---

## 🔄 Branch Strategy

### Main Branches
- **`dev`**: Primary development branch
  - This is where all completed work goes
  - Both versions pull/push here
  - Single source of truth for version control

- **`session` branches**: Temporary branches created by Claude Cloud
  - Format: `origin/claude/[description]-[session-id]`
  - Used during active development in Claude Cloud
  - Should be merged to `dev` after completion (not pushed directly to local)

- **`main`**: Production/release branch
  - Only for tagged releases
  - Reserved for stable versions

---

## 👥 Workflow Rules

### Claude Cloud Responsibilities
1. **During session (session branch)**
   - Work on features/fixes in temporary session branch
   - Make code changes, updates, and improvements

2. **Before finishing a session**
   - ✅ Push session branch to GitHub
   - ✅ Ensure all work is committed in session branch
   - ⚠️ **NOTE**: Claude Local will merge session → `dev` and push to GitHub
   - ⚠️ **Permissions**: Claude Cloud cannot push to `dev` directly (403 restriction)
   - ❌ **DO NOT** push session branch directly to local
   - ❌ **DO NOT** assume local will cherry-pick changes

3. **Session branch push (optional)**

   **When to push session branch to GitHub:**
   - ✅ Creating a PR (need to review changes in GitHub Web UI)
   - ✅ Want to backup work-in-progress to GitHub
   - ✅ Local needs to inspect session branch contents
   - ✅ Collaborating with others on the session branch

   **When NOT to push session branch:**
   - ⏭️ Using direct merge to `dev` (session branch stays local)
   - ⏭️ Session branch is purely temporary/throwaway
   - ⏭️ All work will go to `dev` immediately
   - ⏭️ No need for PR review process

   **Note:** Session branches are temporary by design. Once merged to `dev`, they can be deleted from both local and remote.

4. **When done**
   - Confirm `dev` on GitHub is up-to-date with all changes

### Claude Local Responsibilities
1. **Synchronization**
   - Before starting work: `git fetch origin && git pull origin dev`
   - Keep local copy synchronized with remote `dev`

2. **When Claude Cloud updates `dev`**
   - Pull latest: `git pull origin dev`
   - Take everything (commits, tags, release notes, etc.)

3. **Local-initiated work**
   - Make changes directly on `dev` branch
   - Commit with clear messages
   - Push to `origin/dev` when ready: `git push origin dev`

4. **GitHub Release & Publishing**
   - Create GitHub releases from tags
   - Update documentation on GitHub
   - Handle release workflows

---

## 🔀 Sync Scenarios

### Scenario 1: Claude Cloud finishes work
```
Claude Cloud        GitHub session        GitHub dev        Claude Local
   (session)  ────→  (session) ────→   (merged by Local)  ←──── (pull)
              [push]              [merge + push by Local]
```
1. Claude Cloud pushes session → GitHub session
2. Claude Local pulls GitHub session, merges to `dev`, pushes to GitHub
3. Claude Cloud pulls `dev` in next session (gets everything)

### Scenario 2: Claude Local makes changes
```
Claude Cloud                    GitHub                    Claude Local
   (idle)          ←──────────────(dev)  ←──────────   (dev)
                                         [push]
```
1. Claude Local commits & pushes to `dev`
2. Claude Cloud fetches when starting next session

### Scenario 3: Conflict (both working)
```
Should not happen if following rules!
If it does:
  → dev on GitHub is source of truth
  → Local: git fetch && git pull origin dev (get latest)
  → Cloud: Merge session properly into dev before local pulls
```

---

## 📝 Release Process

1. **Claude Cloud** (in session)
   - Complete all code/feature changes for release
   - Merge everything to `dev` on GitHub

2. **Claude Local** (after pull)
   - Pull all changes from `dev`
   - Create and push tags (e.g., `v0.2.0`)
   - Write release notes
   - Create GitHub Release from tag
   - Publish release

---

## 🚀 Example: v0.2.0 Release

**Claude Cloud session:**
```
1. Create work in session branch
2. Merge session → dev on GitHub
```

**Claude Local:**
```
1. git fetch origin
2. git pull origin dev
3. git tag -a v0.2.0 -m "Release message"
4. git push origin v0.2.0
5. Create release notes (RELEASE_NOTES_v0.2.0.md)
6. gh release create v0.2.0 -F RELEASE_NOTES_v0.2.0.md
7. GitHub Release published ✅
```

---

## 📋 Development Lifecycle

### Specification Confirmation Phase
- **Who**: Claude Cloud (discusses with user)
- **What**: Finalize feature requirements and specifications
- **When**: User confirms feature details
- **Output**: Confirmed specs ready for planning

### Implementation Planning Phase
- **Who**: Claude Cloud
- **What**: Code structure decisions, file locations, implementation approach, coding considerations
- **When**: After specs are confirmed, before coding starts
- **Output**: Plan memory created (e.g., MM259 for v0.2.6)
  - Records: Feature list, implementation notes, scheduling
  - Format: Simple outline with ✅/⏳ status markers

### Implementation Phase
- **Who**: Claude Cloud
- **What**: Feature development and bug fixes
- **When**: After implementation planning is complete
- **Output**: Session branch with commits

### Testing & Release Phase
- **Who**: Claude Local
- **What**: Pull → test → merge → tag → release
- **When**: After implementation is complete and pushed
- **Output**:
  - Plan memory updated (✅ mark for completed features)
  - Detail memory created (e.g., MM300 for implementation specifics)
  - Hub memory updated (MM290 references new records)

### Important Note: Flexibility
This workflow is a guideline for smooth collaboration. Real-world projects may require adjustments due to:
- Unexpected issues during implementation
- Rapid iteration on features
- Claude Local working independently (without Cloud involvement)
- Specification changes mid-development

**If situations arise that don't fit this workflow, adapt as needed.**
Memory records should reflect what actually happened, not force reality into the plan.

---

## ⚠️ Common Mistakes to Avoid

❌ **Claude Cloud**:
- Don't push session branch changes expecting local to cherry-pick
- Don't assume local will find session branch content
- Don't mix multiple sessions in one branch

❌ **Claude Local**:
- Don't work on local branches (stick to `dev`)
- Don't force push (use clean pulls/merges)
- Don't ignore upstream changes

---

## ✅ Checklist for Claude Cloud

Before ending a session:
- [ ] All work committed in session branch
- [ ] Session branch merged to `dev` on GitHub
- [ ] Tags created (if releasing)
- [ ] Release notes/documentation added to `dev`
- [ ] `dev` branch is up-to-date and clean

## ✅ Checklist for Claude Local

Before starting work:
- [ ] `git fetch origin && git pull origin dev`
- [ ] Check for new tags: `git tag -l`
- [ ] Review latest commits: `git log -5 --oneline`

---

## 💡 Code Quality & Best Practices

### Documentation Policy

- **CLAUDE.md**: Generic guidelines and templates only (no project-specific details)
- **Memory system**: Project history, version-specific plans, implementation results
- **Why?** CLAUDE.md is a reusable template for future projects; memory preserves actual project context

### Testing Strategy & Coverage

**Important Reality Check**: All existing tests (49/49) PASS, but bugs still appear in production/interactive features.

**Why?**
- Current tests cover: CLI routing, argument parsing, core utilities, alias management
- Current tests do NOT cover: Interactive features, slash commands, menu interactions, user input parsing
- Test suite is comprehensive for *utility* functions but lacks *integration* and *interaction* tests

**Test Coverage Gap:**
```
✅ Covered:
  - test_cli.py (15): Command routing, argument parsing, error handling
  - test_commands.py (12): List, show, alias, doctor operations
  - test_core.py (22): Alias loading, name resolution, config, rendering, helpers

❌ NOT Covered:
  - Interactive search menu (search_interactive.py)
  - Slash command parsing (/search, /display, /exit)
  - Menu choice parsing (n/f/s/d/0 inputs)
  - User input validation and edge cases
  - Feature interactions (e.g., filters + display count together)
```

**Implementation Rule: Add Tests When Adding New Functions**

Only create test files when NEW FUNCTIONS are added. Don't add tests for every version if no new functions are introduced.

```
When you add a new function:
  ✅ Create test file for it (test_search_vX.Y.Z.py or test_function_name.py)
  ✅ Add tests ONLY for the new function(s)
  ❌ Don't re-test existing functions (they already have tests or are stable)
  ❌ Don't run all 49 tests every time (only run new function tests)

Why?
  - New functions = need quality assurance → create tests
  - Old functions = already tested/stable → skip redundant testing
  - GitHub appearance = "test files exist" proves development care
  - Dev efficiency = avoid running 49 tests for minor changes
```

**Test File Naming:**
```
tests/test_search_vX.Y.Z.py
  └─ Contains tests for NEW functions added in that version
  └─ Each version gets its own test file
```

**Cumulative Test Design (Test File Inheritance)**

When implementing a new version with new functions:

1. **Copy Previous Version's Test File**
   - Rename: `test_search_vX.Y.Z.py` → `test_search_vX.Y.(Z+1).py`
   - Keep all existing test classes and functions from previous version
   - Benefit: Maintains regression protection for stable/old functions

2. **Add New Tests Only for New Functions**
   - Add test classes for newly added functions
   - Don't modify or re-test existing test classes
   - Result: One comprehensive test file per version

3. **Why This Approach?**
   - Avoids test duplication across multiple files
   - Clear ownership: version X tests = test_search_vX.Y.Z.py
   - Regression protection: old function tests are preserved
   - Single source of truth for version functionality

**Example Test Content** (for v0.3.3 with new functions):
```python
# tests/test_search_v0.3.3.py
from commands.search_interactive import parse_menu_choice, parse_slash_command

def test_parse_menu_choice_next_page():
    action, param = parse_menu_choice("n", max_display=10)
    assert action == "next_page"

def test_parse_slash_command_search():
    # /search llama should update query
    result = parse_slash_command("/search llama", query="", state, models=[])
    assert result[1] == "llama"

def test_parse_slash_command_display():
    # /display 20 should set results_per_page to 20
    parse_slash_command("/display 20", query="", state, models=[])
    assert state.results_per_page == 20

def test_parse_slash_command_invalid_old_format():
    # Old /s, /d commands should not work
    result = parse_slash_command("/s llama", query="", state, models=[])
    # Should return None or error, not process
    assert result is None
```

**When to Run Tests:**
```
After adding new functions:
  $ pytest tests/test_search_vX.Y.Z.py -v  # Run only new function tests

Before committing:
  $ pytest tests/ -v  # Full test suite for safety

Don't need to:
  - Run all 49 tests for every minor change
  - Add tests unless you added new functions
  - Test old stable functions repeatedly
```

**Principle**: Tests = Quality Assurance + GitHub Credibility. Add them strategically for new code, not for ceremonial "49/49 PASS" results.

---

### External Library Usage

When integrating external libraries (e.g., prompt-toolkit, MLX), follow these principles:

1. **Verify Official Documentation First**
   - ⚠️ Don't assume library behavior based on previous experience or partial knowledge
   - ✅ Check official docs/source code for:
     - Correct API parameter names and types
     - Special key formats or naming conventions (e.g., `''` for default styles in prompt-toolkit)
     - Version-specific behavior differences
   - 💡 Example: prompt-toolkit uses `''` (empty string) for default style, not `'default'`

2. **Create Adapter/Conversion Layers**
   - ✅ When using library-specific formats, create a conversion layer to your internal format
   - ✅ Store data in standard/portable formats (e.g., ANSI codes for colors, not library-specific codes)
   - ✅ Convert to library format only when needed
   - **Benefit**: Easy library switching, better testability, cleaner separation of concerns
   - Example: `ansi_to_prompt_toolkit_style()` converts ANSI → prompt-toolkit styles

3. **Test Library-Specific Code**
   - ✅ Create unit tests for conversion functions
   - ✅ Pure functions (input → output) are easier to test than integrated code
   - ✅ Mock or isolate library dependencies in tests

4. **Document Non-Obvious Integrations**
   - ✅ Add comments explaining library-specific behavior or "gotchas"
   - ✅ Reference official docs in comments when implementation differs from intuition
   - Example: "Empty string key `''` sets default style for entire input text per prompt-toolkit spec"

---

## 🔗 Repository & Documentation
- **GitHub Repository**: https://github.com/CreamyCappuccino/mlxlm
- `README.md`: Project overview
- `USAGE.md`: User documentation
- `CONTRIBUTING.md`: Contribution guidelines
- **Design Memos**: `/DesignMemo/` - Japanese design documentation for internal reference only

**Tip**: Use `mlxlm search --help-detail` (without query) to get comprehensive search documentation. Works with or without a query argument.

---

## 🌐 Language Policy

**Public-facing content** (GitHub, code, comments, documentation):
- ✅ **English ONLY** - This is an OSS project

**Internal documentation** (design memos, implementation notes):
- ✅ **Japanese** - For author's reference and project documentation
- Location: `/DesignMemo/` folder
- Used for detailed planning, technical rationale, and implementation notes

**Test files and code**:
- ✅ **English ONLY** - No Japanese text in print statements, assertions, or comments

---

## 📌 Memory Management for Claude Instances

### MLX-LM Project Memory Structure

**Three core memories for version management:**
- **MM259**: Master release plan (all versions v0.1.0-v0.3.5+)
  - Single source of truth for what's planned
  - Updated when new versions are added to roadmap
- **MM303**: Implementation results summary (v0.1.0-current)
  - Tracks completed work and results
  - Appended/updated as each version completes
- **MM290**: Navigation hub (references MM259 only)
  - Minimal content: points to MM259 and version memories
  - Used to understand current state
  - Referenced by all version-specific memories

**How to use each session:**
1. Check MM290 → understand current progress and related memories
2. Implement Phase N (code changes)
3. Create/update version memory (MM308, MM309, etc.) with results
4. Update MM303 with completed phase (append, not replace)
5. Update MM259 if planning changes (append rationale)

**Memory growth management:**
- MM259: Append new planned versions at bottom (never delete old ones)
- MM303: Append completed work (maintains complete history)
- MM290: Keep minimal, update only when navigation changes
- Phase details: Create dedicated memory per phase (MM308+)

**Linking rules:**
- Version result memories → link to MM290 + MM303
- Phase detail memories → link to MM290 only
- Avoid forcing chains; link only when there's actual dependency

### General Hub Memory Pattern

**Hub Memory**: Central navigation point, links to plan only
- Example: MM290 → MM259 (plan)

**Detail Memories**: Link to hub + directly related detail memory
- MM291 (report) → MM290, MM259
- MM294 (result) → MM290, MM291 (same report)
- MM295 (result) → MM290, MM291 (same report)
- MM297 (execution) → MM290 only (no direct dependency)

**Rule**: Link only when there's actual sequential or dependency relationship. Avoid forcing chains.

---
