# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-11-07

### Added

- Added `help [command]` to display usage information and guide users within the
  REPL.
- Added diagnostic error messages for incorrect commands: Now the program checks
  if the command is available, and errors if the user input is incorrect.
- Added suggestions for incorrect user input: for example if the user writes
  gem, We'll suggest gen as the most similar command, with up to 2
  recommendations.
- Added error handling for incorrect arguments passed when launching commizard.
  The program now redirects the user to use -h for correct option passing
- Added `--no-color` option: disables color output on stdout and stderr.
- Added `--no-banner` option: suppresses the ASCII banner from being printed.

### Changed

- Bump maximum supported version of dependencies:
    - Rich: 14.1.0 to 14.2.0
    - Pyperclip: 1.9.0 to 1.11.0
- Improved HTTP error handling with clearer status messages and suggested
  fixes (thanks [@bored-arvi](https://github.com/bored-arvi))

### Fixed

- Fixed, optimized and resized the project's banner (
  thanks [@TimBrusten](https://github.com/TimBrusten))
- Removed possible whitespace from the beginning and end of the generated commit
  message
- Fixed vague error message in using `gen`: Now the error message tells the user
  they haven't started a model

## [0.2.0] - 2025-10-20

### Added

- New `cls`/`clear` command to clear the screen (thanks
  [@MRADULTRIPATHI](https://github.com/MRADULTRIPATHI))
- Many additions to the test suite and better DevEx with new CI/CD pipelines,
  including new GitHub workflows, Nox sessions, reaching 100% test coverage,
  addition of e2e tests, addition of dependabot dependency tracking, and
  rewrites for a couple of tests

### Changed

- Updated documents (README.md and CONTRIBUTING.md) (thanks
  [@ryleymao](https://github.com/ryleymao))
- Rewrote the generation portion for clearer control flow and structure
- Standardize development with linters and the ruff formatter (thanks
  [@Aisha630](https://github.com/Aisha630))
- Errors now print to stderr (previously stdout) for better error handling;
  scripts parsing output may need updates

### Fixed

- Fixed blank input crashing the program
- Fixed empty start argument crashing the program
- Fixed `gen`/`generate` crashes on invalid inputs for more reliable usage
- Fixed possible incorrect behavior in executing git diff with possible
  unchecked None return (thanks [@Aisha630](https://github.com/Aisha630))
- Fixed duplicate error messages on `list`
- Optimized startup time by running git, AI, and worktree checks in parallel
  with multithreading, fixing lag from slow AI availability check
- Fixed Python 3.9 support (broken due to type hint issues) to fulfill initial
  compatibility promise (thanks [@bored-arvi](https://github.com/bored-arvi))

## [0.1.0] - 2025-10-01

### Added

- `cp` command to copy the generated message to the clipboard.
- `commit` command to directly commit the generated message without editing.
- A unit test suite (currently 140 tests implemented, with 8 still failing).
- Argument parsing: `-h`, `--help`, `-v`, and `--version` are now supported.
- Added CHANGELOG.md to track notable changes.

### Changed

- Improved and updated `README.md`.
- Moved TODO items to GitHub issues.
- Added dynamic versioning: the project version is now centralized in
  `__init__.py`.
- Improved the diff sent to the LLM, allowing for more accurate commits with
  fewer tokens.
- Added wrapping functionality: Now the commit lines all wrap at 70 lines.
- Refactored significant parts of the codebase. This is still a work in
  progress, but the program’s flow is now cleaner and more maintainable.
- Standardized exit codes. Previously the program would always exit with 0. Now
  the status code varies for errors: 0 for successful exits, 1 for errors (
  thanks [@bored-arvi](https://github.com/bored-arvi))

### Fixed

- Fixed `gen` command crashing when user changes contained certain special
  Unicode characters. Changes containing any UTF-8 supported character are now
  handled correctly.
- Fixed Keyboard interrupts from the user crashing the program. The program will
  now exit gracefully if the user hits Ctrl+C (
  thanks [@bored-arvi](https://github.com/bored-arvi))

## [0.0.1-alpha] - 2025-09-16

### Added

- Basic functionality: `start`, `list`, `gen`, and `quit` commands.
- `README.md` to serve as a welcoming and getting started guide.
- `CONTRIBUTING.md` to help contributors get involved.
- MIT open source license.
- PyPI release: the package can now be installed with `pip install commizard`.

[Unreleased]: https://github.com/Chungzter/CommiZard/compare/v0.3.0...master

[0.3.0]: https://github.com/Chungzter/CommiZard/compare/v0.2.0...v0.3.0

[0.2.0]: https://github.com/Chungzter/CommiZard/compare/v0.1.0...v0.2.0

[0.1.0]: https://github.com/Chungzter/CommiZard/compare/v0.0.1a0...v0.1.0

[0.0.1-alpha]: https://github.com/Chungzter/CommiZard/releases/tag/v0.0.1a0
