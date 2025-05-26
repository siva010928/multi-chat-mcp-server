# Contributing to Multi-Provider MCP Server

Thank you for your interest in contributing to the Multi-Provider MCP Server project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when participating in this project. We expect all contributors to:

- Be respectful and inclusive in communication
- Accept constructive criticism gracefully
- Focus on what's best for the community and project
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/multi-chat-mcp-server.git
   cd multi-chat-mcp-server
   ```
3. **Set up the development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat or .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Process

### Making Changes

1. Make your changes in your feature branch
2. Follow the existing code style and patterns
3. Include comments and docstrings for new code
4. Update any relevant documentation

### Testing

1. We recommend writing tests for new features or bug fixes
2. If you choose to include tests, run the test suite to ensure they pass:
   ```bash
   python -m pytest
   ```
3. For provider-specific tests (optional but recommended):
   ```bash
   python -m pytest src/providers/your_provider
   ```

Testing is flexible and not strictly enforced, but it helps ensure the stability and reliability of your contributions.

### Submitting Changes

1. **Commit your changes** with a clear and descriptive commit message:
   ```bash
   git commit -m "Feature: Add support for new message types"
   ```
2. **Push to your fork**:
   ```bash
   git push origin feature/my-feature
   ```
3. **Create a Pull Request** from your fork to the main repository
4. **Describe your changes** in the PR description:
   - What problem does it solve?
   - How does it work?
   - Any specific areas reviewers should focus on?

## Adding New Providers

If you want to add support for a new chat platform:

1. **Review existing providers** to understand the architecture
2. **Create new provider directory** following the standard structure:
   ```
   src/providers/new_provider/
   ├── api/              # API client implementations
   ├── tools/            # MCP tool implementations
   ├── utils/            # Utility functions
   ├── __init__.py
   ├── mcp_instance.py   # MCP instance configuration
   └── server_auth.py    # Authentication handling
   ```
3. **Add configuration** to `provider-config.yaml`
4. **Implement required interfaces**:
   - Authentication flow
   - API client methods
   - MCP tools
5. **Write tests** for your implementation (recommended)
6. **Document** your provider's features and requirements

For a detailed walkthrough of adding a new provider, please refer to [docs/PROVIDER_SPECIFIC_DEVELOPMENT_WALKTHROUGH.md](docs/PROVIDER_SPECIFIC_DEVELOPMENT_WALKTHROUGH.md).

## Documentation

We value good documentation. For any feature or change:

1. Update relevant README files
2. Add or update docstrings for functions and classes
3. Include examples where appropriate
4. Document any configuration options

## Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in the issue tracker
2. Create a new issue with:
   - A clear title
   - A detailed description
   - Steps to reproduce (for bugs)
   - Expected and actual behavior (for bugs)
   - Version information (Python version, OS, etc.)

## Questions?

If you have any questions about contributing, feel free to open an issue for clarification.

Thank you for contributing to the Multi-Provider MCP Server project! 