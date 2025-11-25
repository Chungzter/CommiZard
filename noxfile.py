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
    run unit tests. Reports code coverage if "cov" argument is sent.
    Generates coverage.xml if "xml" argument is sent.
    """
    if "cov" in session.posargs:
        print("coverage report")
        args = [
            "pytest",
            "--cov=commizard",
            "--cov-report=term-missing",
            "-q",
            "./tests/unit",
        ]
        if "xml" in session.posargs:
            # Insert right after --cov=commizard (index 2)
            args.insert(2, "--cov-report=xml")
    else:
        args = ["pytest", "-q", "./tests/unit"]
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

    if "CI" in session.posargs:
        session.notify("format", ["check"])
        session.notify("test", ["cov", "xml"])

    else:
        session.notify("format")
        session.notify("test")

    if "fix" in session.posargs:
        session.notify("lint", ["fix"])
    else:
        session.notify("lint")


@nox.session(reuse_venv=True, venv_backend=venv_list)
def check_all(session):
    """
    run all checks (used in CI. Use the check session for a faster check)
    """

    if "CI" in session.posargs:
        session.notify("format", ["check"])
        session.notify("test")
    else:
        session.notify("format")
        session.notify("test", ["cov"])

    session.notify("lint")
    session.notify("e2e_test")
