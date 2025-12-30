# Podcast Manager - Codebase Guide for Claude Code

This guide helps Claude Code understand and work effectively with the Podcast Manager codebase.

## Quick Reference

- **Main entry point**: [prepare_for_phone.py](prepare_for_phone.py)
- **Run tests**: `conda activate podcast && python run_tests.py`
- **Type checking**: mypy --strict (REQUIRED)
- **Key dependencies**: FFmpeg 4.2.2, mutagen, pyglet, ADB

## Quick Start for Development

```bash
# 1. Activate environment (REQUIRED for all operations)
conda activate podcast

# 2. Run tests (do this FIRST to verify environment)
python run_tests.py

# 3. Check type compliance before making changes
mypy --strict .

# 4. After making changes, run all quality checks
black .                    # Format code
mypy --strict .           # Type check
python run_tests.py       # Run tests

# 5. Pre-commit hooks will run automatically on commit
```

## Project Overview

**Podcast Manager** is a personal Python application that manages podcast files on a desktop computer and syncs them to an Android phone via ADB. The system:
- Scans podcast show folders for episodes
- Maintains a persistent database of episodes with metadata
- Selects episodes based on priority and time constraints
- Processes audio files (normalization, speed adjustment, metadata updates)
- Transfers processed episodes to Android devices
- Maintains local backups and archives
- Logs all operations for audit purposes

## Architecture

### Core Components

```
prepare_for_phone.py (Main Entry Point)
    ├── PodcastDatabase (podcast_database.py)
    │   └── Manages persistent state, scanning, and episode selection
    ├── AndroidPhone (android_phone.py)
    │   └── Handles ADB connection, file transfer, and history logging
    ├── Settings (settings.py)
    │   └── Loads user configuration and podcast subscriptions
    └── Processing Pipeline
        ├── conversions.py (FFmpeg wrapper for audio processing)
        ├── audio_metadata.py (ID3/MP4 tag manipulation)
        ├── helper.py (Audio preparation orchestration)
        └── backup.py (Local backup management)
```

### Key Data Models

- **PodcastShow** ([podcast_show.py](podcast_show.py)) - Represents a podcast with folder path, priority (P0/P1/P2/SKIP), archive flag, and playback speed
- **PodcastEpisode** ([podcast_episode.py](podcast_episode.py)) - Episode metadata (path, index, duration, modification time)
- **FullPodcastEpisode** ([full_podcast_episode.py](full_podcast_episode.py)) - Enriched episode with show name, speed, and archive status
- **PodcastDatabase** ([podcast_database.py](podcast_database.py)) - Persistent database of shows and episodes

## Main Workflow

1. **Initialization**: Load settings from `user_data/user_settings.json` and podcast subscriptions from `user_data/subscribed_shows.py`
2. **Database Load**: Load or create `user_data/podcast.db` with episode state
3. **Scanning**: Each podcast show scans its folder for new/updated episodes
4. **Selection**: Choose episodes based on:
   - N oldest episodes (configurable)
   - User-specified files from `user_data/specified_files.py`
   - Priority-based selection up to time limit
5. **Processing**: Multi-threaded audio processing:
   - FFmpeg loudness normalization
   - Playback speed adjustment via tempo filter
   - MP3/M4A metadata updates (title with index prefix, album as show name)
   - Optional archive copies
6. **Transfer**: Push processed files to Android device via ADB
7. **Cleanup**: Move successful transfers to backup folder, update database

## Entry Points

### Primary Entry Point
- **[prepare_for_phone.py](prepare_for_phone.py)** - Main script
  - Command: `python prepare_for_phone.py [--dry-run] [--verbose]`
  - Function: `main(args, user_settings)` orchestrates entire workflow

### Test Runner
- **[run_tests.py](run_tests.py)** - Test discovery and execution
  - Command: `python run_tests.py [--failfast] [--pattern <pattern>]`
  - Default pattern: `*_test.py`

### Pre-commit Hook
- **[pre-commit.py](pre-commit.py)** - Pre-commit validation (runs tests)

## Configuration Files

### User Configuration
- **user_data/user_settings.json** - Required settings:
  - `ANDROID_PHONE_ID` - ADB device ID
  - `PODCAST_FOLDER` - Root folder for podcast shows
  - `PODCAST_DIRECTORY_ON_PHONE` - Android device path (e.g., `/sdcard/Podcasts`)
  - `NUM_OLDEST_EPISODES_TO_ADD` - Always include N oldest episodes
  - `TIME_OF_PODCASTS_TO_ADD_IN_HOURS` - Target duration limit
  - `PROCESSED_FILE_BOARDING_ZONE_FOLDER`, `ARCHIVE_FOLDER`, `BACKUP_FOLDER`, `USER_DATA_FOLDER`

- **user_data/subscribed_shows.py** - Python module with `PODCASTS` list of `PodcastShow` instances
- **user_data/specified_files.py** - Python module with `SPECIFIED_FILES` dict for manually specified episodes

### Development Configuration
- **[podcast.yml](podcast.yml)** - Conda environment
- **[.pre-commit-config.yaml](.pre-commit-config.yaml)** - Pre-commit hooks
- **[ruff.toml](ruff.toml)** - Ruff linter configuration
- **[.flake8](.flake8)** - Flake8 linter rules
- **[mypy.ini](mypy.ini)** - Mypy type checker configuration (strict mode enabled)

### Generated State Files (user_data/)

**NOTE**: The `user_data/` folder is in `.gitignore` and contains user-specific configuration and generated files.

Required files (must be created by user):
- `user_settings.json` - User configuration (see Settings section above)
- `subscribed_shows.py` - Python module with `PODCASTS` list
- `specified_files.py` - Python module with `SPECIFIED_FILES` dict

Generated files (created automatically):
- `podcast.db` - Persistent database of episodes (text format)
- `history.txt` - General operation logs
- `android_history.txt` - Android transfer logs
- `backup_history.txt` - Backup operation logs
- `stats.txt` - Statistics about remaining episodes

## Testing

**CRITICAL**: Always run the full test suite before considering any work complete. Tests must pass before submitting code changes.

### Test Structure
- **test files follow *_test.py pattern** for all major modules
- **[e2e_test.py](e2e_test.py)** - End-to-end tests with Android emulator integration
- **[testdata/](testdata/)** - MP3/M4A test files with various metadata scenarios (unicode, emojis, missing tags)
- **[test_utils.py](test_utils.py)** - Shared test utilities

### Running Tests

**Important**: Tests must be run in the `podcast` conda environment. If you get module import errors (like `ModuleNotFoundError: No module named 'mutagen'`), you need to activate the conda environment first.

```bash
# Activate the conda environment
conda activate podcast

# Run all tests
python run_tests.py

# Run with failfast
python run_tests.py --failfast

# Run specific pattern
python run_tests.py --pattern "*_test.py"
```

### Test Expectations
- All tests should pass before code is considered complete
- Some tests include Unicode filenames (Greek characters, emojis) to verify cross-platform compatibility
- End-to-end tests use an Android emulator and take longer to run
- The test runner automatically configures UTF-8 encoding to handle Unicode filenames correctly

## Key Implementation Details

### Priority System
- **P0** - Highest priority (processed first, always included if within time limit)
- **P1** - Medium priority
- **P2** - Lowest priority
- **PRIORITY_SKIP** - Excluded from processing (used for special folders like "Add To Phone", "Archive", "On Phone")

### Audio Processing
- **Normalization**: FFmpeg loudness normalization to -10dB target
- **Speed Adjustment**: FFmpeg atempo filter for playback speed
- **Metadata**: ID3 tags (MP3) or MP4 tags (M4A) updated with:
  - Title: `{episode_index:04d}_{original_title}` (e.g., "0042_Episode Title")
  - Album: Podcast show name
- **Atomic Operations**: Files moved atomically to prevent partial writes

### Multi-threading
- CPU-based thread pool for parallel audio processing
- Subprocess-based processing via [move_file.py](move_file.py)
- Queue-based output collection for progress reporting

### Android Integration
- Uses ADB (Android Debug Bridge) for device communication
- Checks device connectivity before processing
- Pushes files to configured device path
- Logs all transfers to `android_history.txt`
- Removes old backups when files deleted from phone

### Error Handling
- Phone connectivity validation before processing
- Dry-run mode (`--dry-run`) for testing without changes
- Verbose logging (`--verbose`) for debugging
- User confirmation prompts for critical operations
- Atomic file operations to prevent corruption

## Code Quality Standards

This project uses **strict code quality enforcement** with mypy in `--strict` mode. All code must be fully type-annotated.

### Required Tools
- **Type Hints**: Full typing with mypy --strict mode (REQUIRED)
- **Formatting**: Black code formatter
- **Linting**: Flake8 and Ruff (PEP8 naming conventions)
- **Import Sorting**: isort
- **Pre-commit Hooks**: Automated checks before commits

### Code Change Checklist
1. Add complete type hints to all function signatures (mypy --strict compliance)
2. Run `black .` for formatting
3. Ensure `mypy --strict .` passes with zero errors
4. Run full test suite: `python run_tests.py`
5. Pre-commit hooks will validate changes automatically

### Important Type Hints Rules
- All function parameters must have type hints
- All return types must be annotated (including `-> None`)
- Use `typing.List`, `typing.Dict`, etc. for generics (Python 3.13 also supports lowercase)
- Use `pathlib.Path` for file paths, not strings
- Use `typing.Callable` for function parameters

## Files You'll Commonly Edit

### Core Logic
- [prepare_for_phone.py](prepare_for_phone.py) - Main workflow orchestration
- [podcast_database.py](podcast_database.py) - Database management, scanning, selection
- [podcast_show.py](podcast_show.py) - Show management and episode tracking
- [helper.py](helper.py) - Audio processing orchestration

### Audio Processing
- [conversions.py](conversions.py) - FFmpeg wrappers (normalization, speed)
- [audio_metadata.py](audio_metadata.py) - ID3/MP4 tag manipulation
- [move_file.py](move_file.py) - Subprocess-based file processing

### Android Integration
- [android_phone.py](android_phone.py) - ADB operations and transfer logic

### Configuration & Setup
- [settings.py](settings.py) - Settings class and validation
- [command_args.py](command_args.py) - CLI argument parsing

### Data Models
- [podcast_episode.py](podcast_episode.py) - Episode metadata model
- [full_podcast_episode.py](full_podcast_episode.py) - Enriched episode model

### Utilities
- [backup.py](backup.py) - Backup management
- [time_helper.py](time_helper.py) - Duration calculations
- [user_input.py](user_input.py) - User interaction helpers

### Testing
- [test_utils.py](test_utils.py) - Shared test utilities
- [e2e_test.py](e2e_test.py) - End-to-end tests
- Individual `*_test.py` files for each module

## Common Development Tasks

### Adding a New Podcast Show
1. Add folder to `PODCAST_FOLDER` location
2. Create `PodcastShow` instance in `user_data/subscribed_shows.py`
3. Run `prepare_for_phone.py` to scan and add episodes

### Modifying Audio Processing
- **Normalization changes**: Edit `normalize_and_convert()` in [conversions.py](conversions.py)
- **Speed adjustment**: Edit `adjust_speed_of_file()` in [conversions.py](conversions.py)
- **Metadata changes**: Edit [audio_metadata.py](audio_metadata.py)

### Adding Configuration Options
1. Add setting to [settings.py](settings.py) `Settings` class
2. Update `user_data/user_settings.json` schema
3. Add validation in `Settings.__init__()`
4. Update tests in [settings_test.py](settings_test.py)

### Debugging Issues
- Use `--verbose` flag for detailed logging
- Use `--dry-run` flag to test without making changes
- Check `user_data/history.txt` for operation logs
- Review `user_data/android_history.txt` for transfer issues

## Dependencies

### External Tools (Required)
- **FFmpeg** - Audio conversion and processing
- **ADB** - Android Debug Bridge for device communication

### Python Libraries
- **ffmpeg-python** - FFmpeg wrapper
- **mutagen** - Audio metadata manipulation (ID3/MP4 tags)
- **pyglet** - Media file duration detection
- **pre-commit** - Pre-commit hook framework

### Environment Setup
```bash
# Create conda environment from podcast.yml
conda env create -f podcast.yml

# Activate environment
conda activate podcast
```

## File Organization

```
podcast/
├── Core modules (*.py)
│   ├── prepare_for_phone.py (main entry point)
│   ├── podcast_database.py (database management)
│   ├── podcast_show.py (show representation)
│   ├── podcast_episode.py (episode metadata)
│   ├── android_phone.py (ADB integration)
│   └── ... (other core modules)
├── Test files (*_test.py)
├── Test data (testdata/)
├── Configuration files (.pre-commit-config.yaml, mypy.ini, etc.)
├── Environment (podcast.yml)
├── Documentation (README.md, CLAUDE.md)
└── User data (user_data/)
    ├── user_settings.json
    ├── subscribed_shows.py
    ├── specified_files.py
    ├── podcast.db
    └── *.txt (history logs)
```

## Important Notes & Common Pitfalls

### Critical Requirements
1. **Absolute Paths**: `podcast_folder` in `PodcastShow` MUST be absolute paths (enforced in constructor)
2. **Database Format**: Text-based human-readable format (can be manually edited if needed)
3. **Thread Safety**: Database operations are NOT thread-safe (single-threaded scanning/selection)
4. **Conda Environment**: Tests MUST be run in `podcast` conda environment or imports will fail
5. **Type Annotations**: ALL code must pass `mypy --strict` (no exceptions)

### Platform & Encoding
- **Windows Support**: Uses `os.path` and `pathlib` for cross-platform compatibility
- **Unicode Support**: Full Unicode support for filenames and metadata (including emojis)
- **UTF-8 Encoding**: All file operations use `encoding="utf-8"`
- **Atomic Moves**: Files moved atomically via `shutil.move()` to prevent partial writes

### Testing Requirements
- **Always run tests**: Tests MUST pass before code is considered complete
- **Test coverage**: Add tests for any new functionality
- **Unicode tests**: Verify Unicode filename handling (see testdata/)
- **E2E tests**: Require Android emulator setup

## Troubleshooting

### Common Issues
- **ADB not found**: Ensure ADB is in PATH or provide full path to adb executable
- **Phone not connected**: Check `ANDROID_PHONE_ID` matches output of `adb devices`
- **FFmpeg errors**: Verify FFmpeg is installed and in PATH
- **Permission errors**: Ensure write permissions on all configured folders
- **Unicode errors**: Ensure terminal encoding is UTF-8 (handled automatically in [pre-commit.py](pre-commit.py))

### Getting Help
- Review [README.md](README.md) for usage instructions
- Check test files for usage examples
- Examine `user_data/*.txt` logs for operation history
- Use `--verbose` flag for detailed output

## Common Mistakes to Avoid

### DON'T
- ❌ Use relative paths for `podcast_folder` in `PodcastShow` (must be absolute)
- ❌ Run tests outside the `podcast` conda environment
- ❌ Skip type annotations (mypy --strict will fail)
- ❌ Assume database operations are thread-safe (they're NOT)
- ❌ Use string paths instead of `pathlib.Path`
- ❌ Forget to add `encoding="utf-8"` when opening files
- ❌ Create files without running tests first to verify the change works
- ❌ Skip running the full test suite before considering work complete

### DO
- ✅ Use `pathlib.Path` for all file paths
- ✅ Add complete type hints to all functions
- ✅ Run tests after every change: `python run_tests.py`
- ✅ Check mypy compliance: `mypy --strict .`
- ✅ Use `encoding="utf-8"` for all file I/O
- ✅ Test with Unicode filenames (see testdata/ for examples)
- ✅ Use atomic file operations (`shutil.move()`)

## Key Design Patterns

### Object-Oriented Architecture
- **PodcastShow**: Stateful objects that manage their own episodes
- **PodcastDatabase**: Container managing multiple PodcastShow instances
- **Settings**: Immutable configuration loaded at startup
- **AndroidPhone**: Encapsulates all ADB operations

### Functional Approach for Processing
- **conversions.py**: Pure functions wrapping FFmpeg operations
- **audio_metadata.py**: Pure functions for tag manipulation
- **helper.py**: Orchestration functions coordinating processing steps

### Separation of Concerns
- **Database I/O**: Text-based serialization in PodcastShow/PodcastDatabase
- **Audio Processing**: Subprocess-based FFmpeg calls (isolated failures)
- **Android Transfer**: ADB commands isolated in AndroidPhone class
- **Configuration**: Centralized in Settings class

### Error Handling Strategy
- **Validation**: Early validation in constructors (fail fast)
- **User Prompts**: Interactive confirmation for destructive operations
- **Logging**: Comprehensive history logs for audit trail
- **Atomic Operations**: File moves are atomic to prevent corruption

---

## Summary for Claude Code

When working on this codebase:

1. **ALWAYS activate conda environment first**: `conda activate podcast`
2. **ALWAYS run tests to verify changes**: `python run_tests.py`
3. **ALWAYS ensure mypy --strict passes**: No type annotation shortcuts
4. **ALWAYS use `pathlib.Path`**: Never use string paths
5. **ALWAYS use `encoding="utf-8"`**: For all file I/O operations
6. **NEVER use relative paths**: PodcastShow requires absolute paths
7. **NEVER assume thread-safety**: Database operations are single-threaded

This project values:
- **Type safety** (mypy --strict compliance)
- **Test coverage** (16 test files, must all pass)
- **Unicode support** (emojis, Greek characters in filenames)
- **Atomic operations** (prevent corruption on crashes)
- **Clear separation of concerns** (OOP for state, functional for processing)
