# CommiZard

BANNER_IMAGE_TO_BE_ADDED
BADGES_TO_BE_ADDED

CommiZard — An interactive commit assistant, powered by AI!
Generate, tweak, and copy commit messages with full control, right from a REPL.

## Features

- **REPL-style interface** — Stay in an interactive session. Generate multiple
  commit variations without restarting.
- **Smart generation** — Creates commit messages directly from your `git diff`.
- **Simple CLI** — Familiar, intuitive commands. No learning curve.
- **Flexible AI** backends — Easily swap models. Online model support planned!
- **Clipboard magic** — Instantly copy generated messages to your system
  clipboard — ready to paste into `git commit`.
- **Zero daemons** — No background processes. No git hooks. No surprises.
- **Absolute Control** — You run it when *you* want, and you decide to commit,
  copy, tweak, or discard.

## ⚙️ Installation

Install via [pip](https://pip.pypa.io/en/stable/) (from GitHub):

```bash
pip install git+URL_TO_BE_DETERMINED
```

Install from source:

```bash
git clone URL_TO_BE_DETERMINED
cd CommiZard
pip install .
```

Or build using PEP 517 (e.g., with `build` or `hatchling`):

```bash
git clone URL_TO_BE_DETERMINED
cd CommiZard
python -m build
# or: hatchling build
pip install dist/commizard-*-py3-none-any.whl
```

## Usage

IMAGE_TO_BE_ADDED
This is one of the very first times the program helped a user (me 😄) write a
meaningful commit message.

## 🧭 Alternatives & Similar Tools

When I started building CommiZard, I made sure to look around — and guess what?

> CommiZard isn’t the only wizard in town! 😊

If you’re exploring AI-powered commit tools, here are some other great projects
worth checking out:

- **[easycommit](https://github.com/blackironj/easycommit)** — written in go,
  supports Ollama models out of the box.
- **[aicommit](https://github.com/suenot/aicommit)** — Packed with features,
  including a handy VS Code extension.
- **[AICommit2](https://github.com/tak-bro/aicommit2)** — The most complete FOSS
  option I found

> *Why did I still follow through and build this?*  
> Because I couldn’t find a tool that gave me full user control + those little
> UX comforts I craved.  
> So yeah — I built CommiZard for me… and maybe for you too 😉

## Contributing
