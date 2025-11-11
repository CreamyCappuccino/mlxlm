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
   - ✅ Merge session branch into `dev` branch on GitHub (via CLI: `git merge` + `git push`)
   - ✅ Default: Direct merge (no PR needed unless explicitly requested)
   - ✅ Ensure `dev` is updated with all work
   - ❌ **DO NOT** push session branch directly to local
   - ❌ **DO NOT** assume local will cherry-pick changes

3. **When done**
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
Claude Cloud                    GitHub                    Claude Local
   (session)        ────────────→  (dev)  ←─────────  (dev)
     [merge]
```
1. Claude Cloud merges session → `dev`
2. Claude Local: `git pull origin dev` (gets everything)

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

## 🔗 Related Files
- `README.md`: Project overview
- `USAGE.md`: User documentation
- `CONTRIBUTING.md`: Contribution guidelines
- `RELEASE_NOTES_v0.2.0.md`: Release documentation

---
