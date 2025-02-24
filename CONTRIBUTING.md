# Contributing to Eleven Audiobooks

First off, thank you for considering contributing to Eleven Audiobooks! It's people like you that make Eleven Audiobooks such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [project maintainers].

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include any error messages or logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed enhancement
* Examples of how the enhancement would be used
* Any potential drawbacks or challenges

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Process

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev,test]"
```

2. Make your changes:
* Write meaningful commit messages
* Follow the code style guidelines
* Add or update tests as needed
* Update documentation as needed

3. Run the test suite:
```bash
pytest
```

4. Run the linters:
```bash
black .
isort .
ruff check .
mypy .
```

## Style Guidelines

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Style Guide

This project follows:
* [Black](https://black.readthedocs.io/) for code formatting
* [isort](https://pycqa.github.io/isort/) for import sorting
* [ruff](https://beta.ruff.rs/docs/) for linting
* [mypy](https://mypy.readthedocs.io/) for type checking

### Documentation Style Guide

* Use [Google style](https://google.github.io/styleguide/pyguide.html) for docstrings
* Keep docstrings clear and concise
* Include examples in docstrings when helpful
* Update README.md with any new features or changes in requirements

## Additional Notes

### Issue and Pull Request Labels

This project uses the following labels to track issues and pull requests:

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Documentation only changes
* `good first issue` - Good for newcomers
* `help wanted` - Extra attention is needed
* `question` - Further information is requested

## Recognition

Contributors who make significant improvements will be added to the README.md acknowledgments section. 