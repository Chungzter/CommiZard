# How to Contribute to CommiZard

Thank you for your interest in helping shape CommiZard! Here are some ways you
can help improve this project:

## 🐞 Reporting Bugs / Requesting Features

1. First, Check if it's already reported.
   search [open issues](https://github.com/Chungzter/CommiZard/issues).
2. If it's new, [open an issue](https://github.com/Chungzter/CommiZard/issues)!
    - Be as detailed as you can: OS, Python version, steps to reproduce,
      expected vs actual behavior.
    - For feature requests, please describe your use case: why do you need it?

> [!TIP]
> The clearer your report, the faster we can fix or build it!

## ️ Pull Requests (Code Contributions)

### Setting Up for Development

**Prerequisites:**

- [Ollama](https://ollama.ai/) (required only for local LLM API work)
- Nox: this is the standard tool we use for automation.

**Installation:**

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CommiZard.git
   cd CommiZard
   ```

2. Create a virtual environment and install in development mode with dev
   dependencies:
   ```bash
   nox -s venv
   # in linux:
   source ./.nox/venv/bin/activate
   # in windows:
   .\.nox\venv\Scripts\activate
   ```

### Development Workflow

1. If you're working on an issue, please ask to get assigned to that issue.
2. On a new branch from your fork, implement the changes you wish to the project
3. Before committing your changes:

- You can use the nox session to check for possible problems:
    ```bash
    nox -s check
    ```

this session formats the codebase, runs the `ruff check` and `mypy` linters, and
unit tests.

You can run these steps individually with their respective sessions,
and more!

- If you encounter linter problems, you can use the fix argument with the check:
    ```bash
    nox -s check -- fix
    ```
This tries to fix the errors ruff recognizes as 'safe to fix'.

- For example, you can run the e2e tests with `nox -s e2e_test`, or get code
  coverage reports with `nox -s test -- cov`. Use `nox -l` for a full list of
  all available sessions.

4. When you're done, submit a pull request and request a review.
- ✅ I'll review your PR as soon as I can!

Even small fixes like typos, docs, or tests are welcome!

## 🧪 Testing & Quality

Since most of this software is dependent on user input and other software, every
kind of test contribution is appreciated: from adding test cases and increasing
the code coverage with tests, to manually using CommiZard on your system and
giving feedback, every contribution is appreciated.

## Starter Tasks

Not ready to write core features? No problem! These "behind-the-scenes" tasks
are **incredibly valuable**:

- ✍️ **Improve documentation**: Fix typos, clarify confusing sections, add
  examples to README or docstrings.
- **Test on different versions**: Does it work on Python 3.8? 3.10? What
  about different versions of key dependencies (like `ollama`, `requests`,
  `git`)? Report your setup + results!
- 🔗 **Fix broken links or badges**: In README, docs, etc.
- **Improve this CONTRIBUTING.md file**: Make it clearer? More welcoming? Go
  for it!
- 🖼️ **Add example screenshots or asciinema recordings**: Show CommiZard in
  action!
- 🧹 **Run linters & report issues**: Try running other linters like `flake8` or
  `pylint` on the codebase. Found warnings or style inconsistencies? Open an
  issue (or better yet, fix them and push a PR!).

> 💬 Even just asking questions, like "How does this part work?" or "Why is it
> built this way?" can be super helpful. Sometimes explaining it reveals better
> ways to do it!

Need guidance? Just comment on an issue (or open one) saying *"I'd like to help
with this!"*. I'll happily walk you through it.

---

Whether you're reporting a typo or sending a PR, you're helping more than you
know! Thanks in advance.
