# Contributing to MOSS

Thank you for your interest in contributing to MOSS! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in the [Issues](../../issues) section
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - System information (Python version, OS, etc.)

### Submitting Changes

1. **Fork the repository**
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards
4. **Test your changes**:
   ```bash
   python -m pytest tests/
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "Add: description of your change"
   ```
6. **Push and create a Pull Request**

### Coding Standards

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write tests for new functionality
- Keep functions focused and modular

### Commit Message Format

```
Type: Brief description

Detailed explanation if needed.

Types:
- Add: New feature
- Fix: Bug fix
- Update: Modification to existing feature
- Doc: Documentation changes
- Test: Test additions or modifications
- Refactor: Code restructuring
```

### Areas for Contribution

We especially welcome contributions in:

1. **Additional experiments** to validate MOSS framework
2. **Improved objective modules** with better strategies
3. **Safety mechanisms** for self-directed AI
4. **Documentation** and tutorials
5. **Performance optimizations**
6. **Integration** with existing AI frameworks

### Code Review Process

- All PRs require review before merging
- Maintain respectful and constructive communication
- Address feedback promptly
- Ensure CI checks pass

### Questions?

Feel free to open an issue for questions or join discussions.

Thank you for helping advance self-driven AI research!
