# Contributing to TikTok Video Automation Bot

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** from `main`
4. **Make your changes** following our guidelines
5. **Test your changes** thoroughly
6. **Submit a pull request**

## 📋 Development Setup

### Prerequisites
- Python 3.9+ 
- Docker (optional but recommended)
- Git
- FFmpeg (for video processing)

### Local Development
```bash
# Clone your fork
git clone https://github.com/yourusername/BOTTIKTOK.git
cd BOTTIKTOK

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest ruff black isort pytest-cov

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### Docker Development
```bash
# Build development image
docker build -t tiktok-bot-dev .

# Run with mounted source
docker run -v $(pwd):/app -it tiktok-bot-dev bash
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_build_prompt.py -v

# Run specific test
pytest tests/test_bandit.py::TestTrendBandit::test_epsilon_greedy_behavior -v
```

### Writing Tests
- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies
- Aim for >90% code coverage

### Test Structure
```python
import pytest
from unittest.mock import patch, MagicMock

class TestYourModule:
    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        return {"key": "value"}
    
    def test_your_function(self, setup_data):
        """Test description"""
        # Arrange
        # Act
        # Assert
```

## 🎨 Code Style

### Formatting
We use automated code formatting tools:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check . --fix
```

### Style Guidelines
- **Line Length**: 88 characters (Black default)
- **Imports**: Sorted with isort
- **Docstrings**: Google style
- **Type Hints**: Use for function signatures
- **Variable Names**: snake_case
- **Constants**: UPPER_CASE
- **Classes**: PascalCase

### Example Code Style
```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Processes TikTok videos with effects and transformations.
    
    Args:
        config_path: Path to configuration file
        output_dir: Directory for processed videos
    """
    
    def __init__(self, config_path: str, output_dir: str = "output") -> None:
        self.config_path = config_path
        self.output_dir = output_dir
    
    def process_video(self, video_path: str, effects: List[str]) -> Optional[str]:
        """Process video with specified effects.
        
        Args:
            video_path: Path to input video
            effects: List of effects to apply
            
        Returns:
            Path to processed video or None if failed
            
        Raises:
            VideoProcessingError: If processing fails
        """
        try:
            # Implementation here
            return processed_path
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            return None
```

## 📝 Documentation

### Code Documentation
- **Docstrings**: All public functions and classes
- **Comments**: Complex logic and business rules
- **Type Hints**: Function parameters and returns
- **README Updates**: For new features

### Documentation Style
```python
def calculate_engagement_rate(views: int, likes: int, shares: int, comments: int) -> float:
    """Calculate engagement rate for a video.
    
    Engagement rate is calculated as:
    (likes + shares + comments) / views * 100
    
    Args:
        views: Number of video views
        likes: Number of likes
        shares: Number of shares
        comments: Number of comments
        
    Returns:
        Engagement rate as percentage (0-100)
        
    Raises:
        ValueError: If views is zero or negative
        
    Example:
        >>> calculate_engagement_rate(1000, 50, 10, 5)
        6.5
    """
```

## 🔧 Contribution Types

### Bug Fixes
1. **Create an issue** describing the bug
2. **Reference the issue** in your PR
3. **Include tests** that reproduce the bug
4. **Verify the fix** works as expected

### New Features
1. **Discuss the feature** in an issue first
2. **Follow the feature template**
3. **Include comprehensive tests**
4. **Update documentation**
5. **Consider backward compatibility**

### Documentation
1. **Keep it up-to-date** with code changes
2. **Use clear, concise language**
3. **Include examples** where helpful
4. **Test documentation** for accuracy

### Asset Contributions
We welcome community-contributed assets!

#### Background Images/Videos
- **Resolution**: 1080p or higher
- **Format**: JPG, PNG, or MP4
- **Content**: Tech, gaming, AI, data center themes
- **License**: CC0 (public domain) or original work
- **Size**: <50MB per file

#### Overlay Elements
- **Format**: PNG with transparency
- **Resolution**: High quality, scalable
- **Content**: Tech icons, particles, effects
- **License**: CC0 (public domain) or original work

#### Submission Process
1. Create `community-assets/` folder structure:
   ```
   community-assets/
   ├── backgrounds/
   │   ├── tech-datacenter-01.jpg
   │   └── gaming-setup-02.mp4
   └── overlays/
       ├── particle-burst.png
       └── tech-icons.png
   ```
2. Include license information in PR
3. Provide attribution details if required

## 🔒 Security

### Security Guidelines
- **Never commit credentials** or API keys
- **Use environment variables** for sensitive data
- **Validate all inputs** from external sources
- **Follow secure coding practices**
- **Report security issues** privately

### Reporting Security Issues
**Do not create public issues for security vulnerabilities.**

Email security issues to: [security@project.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## 🌍 Internationalization

### Adding Language Support
1. **Create language files** in `locales/`
2. **Use translation keys** in code
3. **Test with different locales**
4. **Update documentation**

### Translation Guidelines
- **Use clear, simple language**
- **Consider cultural context**
- **Test UI layout** with longer text
- **Maintain consistency** across languages

## 📊 Performance

### Performance Guidelines
- **Profile before optimizing**
- **Measure impact** of changes
- **Consider memory usage**
- **Optimize database queries**
- **Use appropriate data structures**

### Performance Testing
```bash
# Profile code
python -m cProfile -o profile.stats your_script.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

## 🚀 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Security scan passed
- [ ] Performance regression tested

## 🤝 Community Guidelines

### Code of Conduct
- **Be respectful** and inclusive
- **Help others** learn and grow
- **Give constructive feedback**
- **Focus on the code**, not the person
- **Follow project guidelines**

### Communication
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Requests**: Code contributions
- **Discord**: Real-time community chat (if available)

### Getting Help
1. **Check existing documentation**
2. **Search existing issues**
3. **Ask in GitHub Discussions**
4. **Create a detailed issue**

## 📋 Checklist for Contributors

### Before Starting
- [ ] Read this contributing guide
- [ ] Check existing issues and PRs
- [ ] Set up development environment
- [ ] Run tests to ensure everything works

### During Development
- [ ] Follow code style guidelines
- [ ] Write tests for new functionality
- [ ] Update documentation as needed
- [ ] Test changes thoroughly

### Before Submitting PR
- [ ] Run full test suite
- [ ] Check code formatting
- [ ] Update CHANGELOG.md
- [ ] Write clear commit messages
- [ ] Fill out PR template completely

## 🎯 Project Roadmap

### Current Priorities
1. **API Resilience**: Improve error handling and retry mechanisms
2. **Performance**: Optimize video processing pipeline
3. **Multi-platform**: Add YouTube Shorts and Instagram Reels support
4. **Community**: Build asset library and contribution tools

### Future Goals
- Advanced AI features
- Real-time analytics dashboard
- Mobile app companion
- Enterprise features

## 📞 Contact

- **Project Maintainer**: [Your Name]
- **Email**: [your.email@domain.com]
- **GitHub**: [@yourusername]
- **Discord**: [Server invite link]

---

Thank you for contributing to the TikTok Video Automation Bot! Your contributions help make this project better for everyone. 🚀
