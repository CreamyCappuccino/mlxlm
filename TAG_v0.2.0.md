# Tag Creation Instructions for v0.2.0

This file contains the instructions for creating the v0.2.0 git tag on your local machine.

---

## Prerequisites

Ensure you have the latest changes from dev branch:

```bash
git checkout dev
git pull origin dev
```

---

## Create Tag v0.2.0

Run the following command to create an annotated tag:

```bash
git tag -a v0.2.0 -m "Release v0.2.0: Test Suite & Documentation

Added comprehensive test suite (49 tests), USAGE guide, and bug fixes.

Changes:
- 49 unit tests for core, commands, and CLI
- Comprehensive USAGE.md documentation
- Fixed model name resolution bug in core.py
- pytest configuration and dev dependencies
- Updated .gitignore for test coverage

Test coverage: 58% overall, 100% for critical components

Features:
- Test suite: test_core.py (22), test_commands.py (12), test_cli.py (15)
- Documentation: USAGE.md (759 lines), CONTRIBUTING.md
- Bug fix: models-- format now correctly resolved
- Infrastructure: pytest.ini, requirements-dev.txt, conftest.py"
```

---

## Push Tag to GitHub

After creating the tag locally, push it to the remote repository:

```bash
git push origin v0.2.0
```

---

## Verify Tag Creation

Check that the tag was created successfully:

```bash
# List all tags
git tag -l

# Show tag details
git show v0.2.0
```

---

## Create GitHub Release

After pushing the tag:

1. Go to: https://github.com/CreamyCappuccino/mlxlm/releases/new

2. Select tag: `v0.2.0`

3. Release title: `Release v0.2.0: Test Suite & Documentation`

4. Description: Copy content from `RELEASE_NOTES_v0.2.0.md`

5. Click "Publish release"

---

## Tag Details

- **Tag name**: v0.2.0
- **Target**: dev branch (latest commit)
- **Type**: Annotated tag (includes message and metadata)
- **Date**: When you create it locally

---

## Troubleshooting

### Tag already exists locally
```bash
# Delete local tag
git tag -d v0.2.0

# Recreate with the command above
```

### Tag already exists on remote
```bash
# Delete remote tag
git push origin :refs/tags/v0.2.0

# Push new tag
git push origin v0.2.0
```

### Permission denied when pushing
- Make sure you have write access to the repository
- Check that you're authenticated with GitHub

---

## What This Tag Represents

v0.2.0 marks the completion of:
- ✅ Comprehensive test infrastructure
- ✅ Complete documentation suite
- ✅ Critical bug fixes
- ✅ Development workflow improvements

This is a significant milestone preparing the project for public release.
