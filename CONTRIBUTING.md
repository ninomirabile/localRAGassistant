# Contributing to Local RAG Assistant

Thank you for your interest in contributing to Local RAG Assistant! This document provides guidelines and information for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/local-rag-assistant.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements/dev.txt`
6. Install pre-commit hooks: `pre-commit install`

## Development Workflow

1. Create a new branch for your feature: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest tests/`
4. Run linting: `black src/ tests/ && isort src/ tests/ && flake8 src/ tests/`
5. Commit your changes: `git commit -m "Add your feature description"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a pull request

## Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Use isort for import sorting
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes

## Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting a pull request
- Use pytest for testing
- Aim for good test coverage

## Pull Request Guidelines

- Provide a clear description of the changes
- Include any relevant issue numbers
- Ensure all tests pass
- Update documentation if necessary
- Follow the existing code style

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment information (OS, Python version, etc.)

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (CC BY-NC 4.0). 