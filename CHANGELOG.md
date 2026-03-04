# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.2] - 2026-03-04

### Added

- **Modular init script architecture** - Refactored init.sh and init.bat into 8 reusable modules
- **Smart uv detection** - Support 10+ installation paths (PATH, homebrew Intel/ARM, npm, pip, cargo, .local/bin, etc.)
- **Multiple installation methods** - Interactive installer supporting homebrew/npm/pip/cargo/curl/scoop (6 methods)
- **Network retry mechanism** - 3 retry attempts with exponential backoff for downloads
- **Error diagnosis** - Intelligent error analysis and fix suggestions
- **State persistence** - JSON-based state management supporting resume and checkpoint recovery
- **Diagnostic information** - Save diagnostic info to ~/.xmind2cases/diagnostics/ for troubleshooting

### Changed

- **init.sh** - Reduced from 821 lines to 313 lines (62% reduction) through modularization
- **Better error handling** - Unified error handling interface across all initialization steps
- **Improved port handling** - Auto-find available ports instead of failing on port conflicts
- **Enhanced shell compatibility** - Better support for zsh, bash, and different platforms

### Fixed

- **uv detection issues** - Fixed uv not being detected after installation via curl
- **PATH persistence** - Automatically configure PATH in shell config files (.zshrc, .bashrc)
- **Permission handling** - Graceful fallback when lacking write permissions

### Documentation

- Add `docs/scripts-architecture.md` - Comprehensive architecture documentation
- Add module design principles and extension guide
- Update README with new features and improvements

## [1.7.1] - 2026-03-04

### Added

- Add MIT LICENSE file to the repository

### Fixed

- Fix README navigation links by adding HTML anchor IDs to all major sections
- Fix README badges by removing invalid ones (GitHub Release, CI Status, Downloads)
- Update README example code to use existing test files
- Remove absolute language ("currently the only tool") for more neutral description

### Changed

- Optimize README structure to highlight core feature: dual-format XMind parsing
- Add acknowledgments section to credit xmind2testcase and xmindparser projects
- Improve README badges to only show working ones (PyPI, Python, License, Last Commit)

### Documentation

- Update README to emphasize XMind 8 (XML) and XMind 2026 (JSON) dual-format support
- Add proper acknowledgments to open source projects this project is based on

## [1.7.0] - 2026-03-04

### Removed

- Remove incomplete FastAPI REST API implementation
- Remove FastAPI related directories: `api/`, `migrations/`, `tests/api/`
- Remove FastAPI dependencies:
  - fastapi, uvicorn[standard]
  - sqlalchemy[asyncio], aiosqlite, alembic
  - pydantic, pydantic-settings
  - python-multipart, httpx, structlog
- Remove `alembic.ini` configuration file

### Changed

- CLI command `xmind2cases webtool` now launches Flask Web tool instead of FastAPI
- Update README.md to remove FastAPI startup instructions
- Update `init.bat` startup script
- Update `pyproject.toml` dependencies configuration
- Clean up `.vscode/settings.json` to remove FastAPI related spellcheck words

### Performance

- Virtual environment size reduced by ~100MB (150MB → 51MB, -66%)
- Dependency installation speed improved
- Project startup speed improved

### Code Quality

- Delete 2,921 lines of incomplete code
- Simplify project structure and improve maintainability
- All tests passing (19/19)

### Breaking Changes

- ⚠️ **FastAPI REST API has been completely removed**
- The `xmind2cases webtool` command now launches Flask Web tool instead of FastAPI
- Core functionality remains fully available: CLI, Flask Web tool, Python API

### Migration Guide

If you previously used the FastAPI version:

1. Flask Web tool provides the same functionality
2. Use `uv run python webtool/application.py` to start
3. Or use the command: `xmind2cases webtool` (default port 5002)

## [1.6.1] - 2026-03-04

### Added

- Support Windows one-click startup (init.bat/init.ps1)
- Port detection and interactive handling
- UI improvements: iconized operations, compact layout, smart filename truncation

### Changed

- Rename package from xmind2testcase to xmind2cases
- Optimize documentation structure, remove duplicate content

### Fixed

- Fix Zentao CSV export format: wrap all fields with double quotes
- Fix newline conversion to `<br>` tags in preconditions

## [1.6.0] - 2026-03-03

### Added

- One-click initialization script init.sh with environment setup and release workflow
- Python minimum version raised to 3.12.12
- Integrate modern development tools: ruff, pyright, pre-commit, rich
- Support XMind 2026 file format (JSON format)
- Support XMind 8 and earlier versions (XML format)
- Add comprehensive test suite (unit, integration, E2E)
- Add project development documentation

### Changed

- Rename project to xmind2cases (formerly xmind2testcase)
- Use uv instead of setuptools for building and publishing
- Switch underlying parsing library from xmind to xmindparser
- Stricter error handling: raise exceptions for missing or malformed files
- Improve data validation and error messages
- Update all documentation and command names

### Removed

- Remove obsolete configuration files: pytest.ini, requirements.txt
- Drop support for Python versions < 3.12.12

### Fixed

- Fix xmind2026 file parsing encoding issues

### Technical Details

- Add `normalize_xmind_data()` adapter function for field mapping
- Field mapping: `makers` → `markers`, `labels` → `label`
- Test coverage reaches 56%+
- Total test count: 19 (11 unit tests + 6 integration tests + 2 E2E tests)

### Testing

- ✅ xmind8 file parsing and conversion verified
- ✅ xmind2026 file parsing and conversion verified
- ✅ Both format output consistency verified
- ✅ CSV, XML, JSON conversion functionality verified

---

**[Compare versions](https://github.com/koco-co/xmind2cases/compare/v1.6.1...v1.7.0)**
