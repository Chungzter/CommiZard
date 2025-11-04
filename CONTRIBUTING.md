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
- Nox (optional, highly recommended for the smoothest workflow)

**Installation:**

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CommiZard.git
   cd CommiZard
   ```

2. Install in development mode with dev dependencies:
   ```bash
   pip install -e .[dev]
   ```

### Development Workflow

Before committing your changes:

1. Format your code:
   ```bash
   ruff format
   ```

2. Lint with Ruff:
   ```bash
   ruff check
   ```

3. Type check with mypy (optional but recommended):
   ```bash
   mypy .
   ```

4. Run tests:
   ```bash
   pytest
   ```

   Or with coverage:
   ```bash
   pytest --cov=commizard tests/
   ```

> [!TIP]
> Run `ruff format && ruff check` before every commit to keep code style
> consistent!

✅ I'll review your PR as soon as I can!

✅ Even small fixes like typos, docs, or tests are welcome!

## 🧪 Testing & Quality

Since most of this software is dependent on user input and other software, every
kind of test contribution is appreciated: from adding test cases and increasing
the code coverage with tests, to manually using CommiZard on your system and
giving feedback, every contribution is appreciated.

## Starter Tasks

Not ready to write core features? No problem! These “behind-the-scenes” tasks
are **incredibly valuable**:

- ✍️ **Improve documentation**: Fix typos, clarify confusing sections, add
  examples to README or docstrings.
- **Test on different versions**: Does it work on Python 3.8? 3.10? What
  about different versions of key dependencies (like `ollama`, `requests`,
  `git`)? Report your setup + results!
- 🔗 **Fix broken links or badges**: In README, docs, etc.
- **Improve this CONTRIBUTING.md file**: Make it clearer? More welcoming? Go
  for it!
- 🖼️ **Add example screenshots or asciinema recordings** — Show CommiZard in
  action!
- 🧹 **Run linters & report issues**: Try running other linters like `flake8` or
  `pylint` on the codebase. Found warnings or style inconsistencies? Open an
  issue (or better yet, fix them and push a PR!).

> 💬 Even just asking questions — like "How does this part work?" or "Why is it
> built this way?" can be super helpful. Sometimes explaining it reveals better
> ways to do it!

Need guidance? Just comment on an issue (or open one) saying *"I'd like to help
with this!"*. I’ll happily walk you through it.

---

Whether you’re reporting a typo or sending a PR, you’re helping more than you
know! Thanks in advance.
