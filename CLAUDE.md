# 🤖 MLX-LM Development Workflow Guide

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

## 🔗 Related Files
- `README.md`: Project overview
- `USAGE.md`: User documentation
- `CONTRIBUTING.md`: Contribution guidelines
- `RELEASE_NOTES_v0.2.0.md`: Release documentation

---

## 📌 Memory Management for Claude Instances

**Hub Memory**: Central navigation point, links to plan only
- Example: MM290 → MM259 (plan)

**Detail Memories**: Link to hub + directly related detail memory
- MM291 (report) → MM290, MM259
- MM294 (result) → MM290, MM291 (same report)
- MM295 (result) → MM290, MM291 (same report)
- MM297 (execution) → MM290 only (no direct dependency)

**Rule**: Link only when there's actual sequential or dependency relationship. Avoid forcing chains.

---
