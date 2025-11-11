# 🎉 Release v0.2.0: Test Suite & Documentation

## ✨ What's New

### Testing Infrastructure
- Added comprehensive test suite with **49 unit tests**
  - `test_core.py` (22 tests): Alias loading, name resolution, rendering, helper utilities
  - `test_commands.py` (12 tests): Model listing, info display, alias management, diagnostics
  - `test_cli.py` (15 tests): CLI routing, argument parsing, error handling
- Test coverage: 58% overall, 100% for critical components
- pytest configuration and development dependencies
- MLX mocking support for cross-platform testing (works on Linux!)

### Documentation
- **USAGE.md** (759 lines): Comprehensive user guide
  - Complete command reference with examples
  - Environment variables documentation
  - Common workflows and use cases
  - Troubleshooting guide
  - Advanced usage patterns
  - Tips and tricks
- **CONTRIBUTING.md**: Developer contribution guidelines
- All code and comments in English for international collaboration

### Bug Fixes
- Fixed `resolve_model_name()` in `core.py` incorrectly handling `models--` format
  - Before: `models--google--gemma-3-27b-it` → Error (invalid conversion)
  - After: `models--google--gemma-3-27b-it` → `google/gemma-3-27b-it` ✅
- This bug affected direct cache key usage; alias-based usage was unaffected

## 📦 What's Included

### New Files
- `tests/__init__.py` - Test package initialization
- `tests/conftest.py` - pytest fixtures and MLX mocking
- `tests/test_core.py` - Core functionality tests (296 lines)
- `tests/test_commands.py` - Command implementation tests (340 lines)
- `tests/test_cli.py` - CLI routing tests (203 lines)
- `pytest.ini` - pytest configuration
- `requirements-dev.txt` - Development dependencies
- `USAGE.md` - Comprehensive user guide (759 lines)

### Updated Files
- `core.py` - Bug fix in model name resolution
- `.gitignore` - Added test coverage exclusions

## 🔧 Installation

```bash
git clone https://github.com/CreamyCappuccino/mlxlm.git
cd mlxlm
pip install mlx-lm huggingface-hub
./install.sh
```

## 🧪 Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

All 49 tests pass successfully on both macOS (Apple Silicon) and Linux environments.

## 📚 Documentation

- [README.md](README.md) - Quick start guide and feature overview
- [USAGE.md](USAGE.md) - Comprehensive usage guide with examples
- [CONTRIBUTING.md](CONTRIBUTING.md) - Developer contribution guidelines

## 🆚 Comparison with v0.1.0

| Feature | v0.1.0 | v0.2.0 |
|---------|--------|--------|
| Core functionality | ✅ | ✅ |
| Test suite | ❌ | ✅ 49 tests |
| Test coverage | 0% | 58% |
| USAGE guide | ❌ | ✅ 759 lines |
| CONTRIBUTING guide | ❌ | ✅ |
| Bug fixes | - | ✅ Model name resolution |
| Code comments | Mixed | 100% English |

## 🚀 Next Steps

After installing v0.2.0:

1. **Verify installation:**
   ```bash
   mlxlm doctor
   ```

2. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

3. **Read the guides:**
   - [USAGE.md](USAGE.md) for detailed usage
   - [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute

## 🔮 Future Plans (v0.3.0+)

- Logging functionality
- Auto-sync models after pull
- Performance optimizations
- Additional test coverage

## 🙏 Acknowledgments

This release was developed collaboratively with Claude Code, demonstrating the power of human-AI pair programming! 🤖✨

Special thanks to the MLX team at Apple and the open-source community.

---

**Full Changelog**: https://github.com/CreamyCappuccino/mlxlm/compare/v0.1.0...v0.2.0
