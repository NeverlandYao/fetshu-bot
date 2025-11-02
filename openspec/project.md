# Project Context

## Purpose
A Feishu (Lark) bot that integrates with Coze AI to provide intelligent conversational capabilities. The bot uses FastAPI as a web framework to handle incoming messages and webhooks from Feishu, and leverages the Coze platform for AI-powered responses.

## Tech Stack
- **Language**: Python 3.14+
- **Web Framework**: FastAPI (with standard extras)
- **AI Integration**: Coze API (cozepy >= 0.20.0)
- **Package Manager**: uv (modern, fast Python package installer)
- **Task Runner**: just (command runner for common tasks)
- **Code Quality**: ruff (linter and formatter)

## Project Conventions

### Code Style
- **Formatter**: Ruff with the following settings:
  - Line length: 88 characters
  - Quote style: double quotes
  - Indent style: spaces
  - Line ending: LF (Unix style)
  - Docstring code formatting: enabled
- **Linter**: Ruff with enabled rules:
  - F: Pyflakes (error detection)
  - E/W: Pycodestyle (style guide enforcement)
  - I001: isort (import sorting)
  - Max complexity: 10 (McCabe)
- Run linting/formatting via: `uv run ruff check` and `uv run ruff format`

### Architecture Patterns
- **Monolithic FastAPI application** with modular structure
- Entry points:
  - `src/bootstrap.py`: Main entry point
  - `src/app.py`: FastAPI application setup
- Use async/await patterns for I/O operations (FastAPI standard)
- RESTful API endpoints for webhook handling

### Testing Strategy
[To be defined - add your testing requirements here]
- Consider adding pytest for unit and integration tests
- Test Feishu webhook handlers
- Mock Coze API calls in tests

### Git Workflow
- **Main Branch**: `main`
- No pre-commit hooks currently configured
- Follow conventional commit messages when possible
- Use feature branches for new work

## Domain Context
- **Feishu/Lark**: Enterprise communication platform (Chinese market)
  - Webhooks for message events
  - Bot authentication and message sending APIs
- **Coze Platform**: AI agent building platform
  - Provides conversational AI capabilities
  - API for sending messages and receiving responses

## Important Constraints
- **Python Version**: Requires Python >= 3.14.0
- **Runtime**: Application runs via `uv run` for dependency management
- Must handle Feishu webhook signatures and encryption
- Rate limiting considerations for both Feishu and Coze APIs

## External Dependencies
- **Feishu/Lark Open Platform**: Message webhooks and bot APIs
  - Authentication tokens required
  - Webhook verification needed
- **Coze Platform**: AI conversation API
  - API keys/tokens required
  - Usage quotas may apply
