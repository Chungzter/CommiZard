import nox  # type: ignore

venv_list: str = "uv|virtualenv"


@nox.session(reuse_venv=True, venv_backend=venv_list)
def venv(session):
    """
    Set up the development environment.
    """
    session.install("-e", ".[dev]")


@nox.session(reuse_venv=True, venv_backend=venv_list)
def lint(session):
    """
    ruff check . && mypy .
    """
    if "fix" in session.posargs:
        session.run("ruff", "check", ".", "--fix", external=True)
        session.log("Ran Ruff with --fix argument to do safe fixes")
    else:
        session.run("ruff", "check", ".", external=True)
    session.run("mypy", ".", external=True)


@nox.session(reuse_venv=True, venv_backend=venv_list)
def test(session):
    """
    run unit tests. returns coverage report if "cov" posarg is sent
    """
    if "cov" in session.posargs:
        print("coverage report")
        args = (
            "pytest",
            "--cov=commizard",
            "--cov-report=term-missing",
            "-q",
            "./tests/unit",
        )
    else:
        args = ("pytest", "-q", "./tests/unit")
    session.run(*args, external=True)


@nox.session(reuse_venv=True, venv_backend=venv_list)
def format(session):  # noqa: A001
    """
    format codebase.
    """
    if "check" in session.posargs:
        session.run("ruff", "format", "--check", external=True)
    else:
        session.run("ruff", "format", ".", external=True)


@nox.session(reuse_venv=True, venv_backend=venv_list)
def e2e_test(session):
    """
    run e2e tests (Warning: It's slow)
    """
    session.run("pytest", "-q", "./tests/e2e", external=True)


@nox.session(reuse_venv=True, venv_backend=venv_list)
def check(session):
    """
    run formatter, linter and shallow tests
    """

    # don't format and just check if we're running this session with CI arg
    if "CI" in session.posargs:
        session.notify("format", ["check"])
    else:
        session.notify("format")
    if "fix" in session.posargs:
        session.notify("lint", ["fix"])
    else:
        session.notify("lint")
    session.notify("test")


@nox.session(reuse_venv=True, venv_backend=venv_list)
def check_all(session):
    """
    run all checks (used in CI. Use the check session for a faster check)
    """

    # don't format and just check if we're running this session with CI arg
    if "CI" in session.posargs:
        session.notify("format", ["check"])
    else:
        session.notify("format")

    session.notify("lint")
    session.notify("test", ["cov"])
    session.notify("e2e_test")
