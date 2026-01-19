# Contributing to Industrial MCP

Thank you for your interest in contributing to Industrial MCP! 🎉

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [Issues](https://github.com/YOUR_USERNAME/industrial-mcp/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, hardware)

### Suggesting Features

1. Open a [Feature Request](https://github.com/YOUR_USERNAME/industrial-mcp/issues/new?template=feature_request.md)
2. Describe the use case and proposed solution
3. Discuss with maintainers before implementing

### Code Contributions

#### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/industrial-mcp.git
cd industrial-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

#### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our code style

3. Write/update tests:
   ```bash
   pytest tests/
   ```

4. Run linting:
   ```bash
   ruff check .
   mypy src/
   ```

5. Commit with clear messages:
   ```bash
   git commit -m "feat: add support for BACnet protocol"
   ```

6. Push and create a Pull Request

#### Commit Message Format

We use [Conventional Commits](https://conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### Adding a New Protocol Adapter

1. Create a new file in `src/industrial_mcp/adapters/`
2. Inherit from `BaseAdapter`
3. Implement required methods: `connect()`, `disconnect()`, `read()`, `write()`
4. Add tests in `tests/adapters/`
5. Update documentation

Example skeleton:

```python
from industrial_mcp.adapters.base import BaseAdapter

class MyProtocolAdapter(BaseAdapter):
    @property
    def protocol_name(self) -> str:
        return "myprotocol"
    
    async def connect(self) -> bool:
        # Implementation
        pass
    
    async def disconnect(self) -> None:
        # Implementation
        pass
    
    async def read(self, address) -> Any:
        # Implementation
        pass
    
    async def write(self, address, value) -> bool:
        # Implementation
        pass
```

## Code Style

- Python 3.10+ syntax
- Type hints required
- Docstrings for all public functions
- Maximum line length: 88 characters
- Use `async/await` for I/O operations

## Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use `pytest-asyncio` for async tests
- Mock external hardware for unit tests

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## Questions?

- Open a [Discussion](https://github.com/YOUR_USERNAME/industrial-mcp/discussions)
- Join our [Discord](https://discord.gg/industrial-mcp)

Thank you for helping make Industrial MCP better! 🏭
