# VS Code Extensions Setup Guide for QuikScribe Backend

This guide will help you install all the necessary VS Code extensions for optimal development experience with your QuikScribe backend project.

## 🚀 Quick Installation

### Option 1: Automated Installation (Recommended)
```bash
# Make sure you're in the project root directory
cd /home/voidraghav/Desktop/Quikscribe-AWS/backend-quikscribe

# Run the installation script
./install_vscode_extensions.sh
```

### Option 2: Manual Installation
If the automated script doesn't work, you can install extensions manually through VS Code.

## 📋 Required Extensions

### Core Python Development
- **Python** (`ms-python.python`) - Essential Python support
- **Pylance** (`ms-python.vscode-pylance`) - Advanced Python language server
- **Python Indent** (`kevinrose.python-indent`) - Smart Python indentation
- **Python Docstring Generator** (`njpwerner.autodocstring`) - Auto-generate docstrings

### FastAPI & Web Development
- **FastAPI Snippets** (`tamasfe.even-better-toml`) - FastAPI code snippets
- **REST Client** (`humao.rest-client`) - Test API endpoints
- **Thunder Client** (`rangav.vscode-thunder-client`) - Alternative REST client

### TypeScript/JavaScript Development
- **Bun** (`oven.bun-vscode`) - Bun runtime support
- **ES7+ React/Redux/React-Native snippets** (`dsznajder.es7-react-js-snippets`) - TypeScript snippets

### Database & ORM
- **SQLTools** (`mtxr.sqltools`) - Database management
- **SQLTools PostgreSQL** (`mtxr.sqltools-postgresql`) - PostgreSQL driver

### Environment & Configuration
- **DotENV** (`mikestead.dotenv`) - .env file syntax highlighting
- **YAML** (`redhat.vscode-yaml`) - YAML file support
- **TOML** (`tamasfe.even-better-toml`) - TOML file support

### Docker & Kubernetes
- **Docker** (`ms-azuretools.vscode-docker`) - Docker container management
- **Kubernetes** (`ms-kubernetes-tools.vscode-kubernetes-tools`) - K8s support

### Git & Version Control
- **GitLens** (`eamodio.gitlens`) - Enhanced Git capabilities
- **Git History** (`donjayamanne.githistory`) - View Git history

### Code Quality & Formatting
- **Black Formatter** (`ms-python.black-formatter`) - Python code formatting
- **isort** (`ms-python.isort`) - Python import sorting
- **Prettier** (`esbenp.prettier-vscode`) - Code formatting
- **ESLint** (`dbaeumer.vscode-eslint`) - JavaScript/TypeScript linting

### Testing & Debugging
- **Python Test Explorer** (`littlefoxteam.vscode-python-test-adapter`) - Python testing
- **Coverage Gutters** (`ryanluker.vscode-coverage-gutters`) - Code coverage

### Productivity & Utilities
- **Auto Rename Tag** (`formulahendry.auto-rename-tag`) - Auto-rename HTML/XML tags
- **Bracket Pair Colorizer** (`coenraads.bracket-pair-colorizer-2`) - Colorize brackets
- **Path Intellisense** (`christian-kohler.path-intellisense`) - Path autocomplete
- **Material Icon Theme** (`pkief.material-icon-theme`) - Better file icons

## ⚙️ VS Code Settings

The project includes optimized VS Code settings in `.vscode/settings.json`:

- Python interpreter path set to `.venv_quikscribe/bin/python`
- Auto-formatting on save with Black
- Auto-import organization
- File associations for .env, .toml, .yaml files
- Optimized search and file watching exclusions

## 🔧 Post-Installation Setup

### 1. Restart VS Code
After installing all extensions, restart VS Code for changes to take effect.

### 2. Select Python Interpreter
1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose `.venv_quikscribe/bin/python`

### 3. Install Python Dependencies
```bash
# Activate virtual environment
source .venv_quikscribe/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Install Node.js Dependencies (for Google Bot)
```bash
cd google_bot
npm install
# or if using Bun
bun install
```

## 🎯 Project-Specific Features

### Python Development
- FastAPI IntelliSense and auto-completion
- SQLAlchemy model support
- Pydantic validation highlighting
- Alembic migration support

### TypeScript/JavaScript Development
- Bun runtime integration
- Express.js development support
- AWS SDK autocompletion
- Selenium WebDriver support

### Database Development
- PostgreSQL connection management
- SQL query execution and results viewing
- Database schema exploration

### API Development
- FastAPI endpoint testing
- OpenAPI documentation generation
- Request/response inspection

## 🚨 Troubleshooting

### Extensions Not Installing
1. Check if VS Code is up to date
2. Verify internet connection
3. Try installing one extension at a time

### Python Interpreter Issues
1. Ensure virtual environment exists
2. Check Python path in settings
3. Reload VS Code window

### Formatting Not Working
1. Check if Black is installed: `pip install black`
2. Verify format on save is enabled
3. Check file associations

## 📚 Additional Resources

- [VS Code Python Extension Documentation](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Bun Documentation](https://bun.sh/docs)

## 🎉 You're All Set!

With these extensions installed, you'll have:
- ✅ Professional Python development environment
- ✅ FastAPI development tools
- ✅ TypeScript/JavaScript support
- ✅ Database management capabilities
- ✅ Docker and Kubernetes integration
- ✅ Git workflow enhancements
- ✅ Code quality and formatting tools

Happy coding with your QuikScribe backend project! 🚀
