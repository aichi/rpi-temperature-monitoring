# Contributing to Raspberry Pi Temperature Monitor

We welcome contributions to the Raspberry Pi Temperature Monitor project! This document provides guidelines for contributing.

## Ways to Contribute

### 1. Reporting Issues
- Use the GitHub Issues tab to report bugs
- Include system information (Raspberry Pi model, OS version)
- Provide clear steps to reproduce the issue
- Include relevant log files if possible

### 2. Feature Requests
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain why it would be valuable to other users

### 3. Code Contributions
- Fork the repository
- Create a feature branch from `master`
- Make your changes with clear, descriptive commits
- Test your changes thoroughly
- Submit a pull request

## Development Setup

1. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/rpi-temperature-monitoring.git
   cd rpi-temperature-monitoring
   ```

2. **Set up the development environment:**
   ```bash
   ./scripts/setup_sudo.sh
   python3 scripts/test_system.py
   ```

3. **Run tests before submitting:**
   ```bash
   python3 scripts/test_system.py
   ```

## Code Guidelines

### Python Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Include docstrings for functions and classes
- Keep functions focused and single-purpose

### Shell Scripts
- Use bash for shell scripts
- Include error handling
- Make scripts portable when possible
- Add usage help text

### Documentation
- Update README.md for user-facing changes
- Add docstrings to new functions
- Update configuration examples
- Include setup instructions for new features

## Plugin Development

To create a new sensor plugin:

1. **Create plugin file** in `collector/plugins/`
2. **Inherit from TemperatureSensorPlugin**
3. **Implement required methods:**
   - `read_temperature()`
   - `is_available()`
   - `get_sensor_info()`

4. **Add to plugin registry** in `collector/plugins/__init__.py`
5. **Test thoroughly** with the test system
6. **Document configuration** in README.md

### Example Plugin Structure
```python
from . import TemperatureSensorPlugin

class MyNewSensorPlugin(TemperatureSensorPlugin):
    def __init__(self, name, config):
        super().__init__(name, config)
        # Initialize your sensor
    
    def read_temperature(self):
        # Read and return temperature
        pass
    
    def is_available(self):
        # Check if sensor is available
        return True
    
    def get_sensor_info(self):
        # Return sensor information
        return {'type': 'MyNewSensor'}
```

## Testing

### Running Tests
```bash
# Run system tests
python3 scripts/test_system.py

# Test specific components
python3 collector/temperature_collector.py  # Test collector
python3 server/web_server.py                # Test server
```

### Test Coverage
- Test basic functionality (CPU, GPU temperature reading)
- Test storage device detection
- Test plugin loading and sensor reading
- Test configuration validation
- Test database operations

## Commit Message Guidelines

Use clear, descriptive commit messages:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Examples:
```
feat: add support for BMP280 temperature sensor
fix: handle missing storage device gracefully
docs: update plugin development guide
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes and test:**
   ```bash
   # Make changes
   python3 scripts/test_system.py
   ```

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add my new feature"
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/my-new-feature
   ```

5. **Submit a pull request** via GitHub

### Pull Request Requirements
- [ ] Code follows project style guidelines
- [ ] Tests pass (`python3 scripts/test_system.py`)
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive data included

## Release Process

For maintainers:

1. **Update version** in relevant files
2. **Test thoroughly** on different Pi models
3. **Update CHANGELOG.md**
4. **Create release tag:**
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push --tags
   ```
5. **Create GitHub release** with release notes

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community support
- **README.md**: For setup and usage instructions
- **docs/**: For detailed documentation

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow GitHub's community guidelines

Thank you for contributing to the Raspberry Pi Temperature Monitor project!
