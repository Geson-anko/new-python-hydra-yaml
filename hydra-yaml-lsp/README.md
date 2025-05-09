# 🐉 hydra-yaml-lsp

![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Document Style](https://img.shields.io/badge/%20docstyle-google-3666d6.svg)

**hydra-yaml-lsp** is a Language Server Protocol implementation for [Hydra](https://hydra.cc) YAML configuration files, providing rich language features like code completion, syntax validation, and semantic highlighting to enhance the development experience with Hydra configuration files.

## ✨ Features

- 💡 Intelligent code completion for Hydra special keys (`_target_`, `_args_`, etc.)
- 🔍 Path completion for Python import paths in `_target_` values
- 🛠️ Argument completion for callable targets
- 🎨 Semantic token highlighting for special keys, target values, and interpolations
- ⚠️ YAML syntax validation and diagnostics
- 🔄 Support for Hydra interpolations (`${...}` syntax)
- 🔌 Easy integration with editor extensions (primary integration with VS Code)

## 📦 Installation

```bash
# Install with pip
pip install hydra-yaml-lsp

# For development setup
git clone https://github.com/your-repo/python-hydra-yaml.git
cd python-hydra-yaml/hydra-yaml-lsp
make venv  # Sets up virtual environment with all dependencies
```

## 🧰 Requirements

- Python 3.12+
- hydra-core>=1.3.2
- pygls>=1.3.1
- ruamel-yaml>=0.18.10

## 📝 Usage

### Standalone Server

```sh
python -m hydra_yaml_lsp
```

### Using with VS Code Extension

The primary use case is through the VS Code extension:

1. Install the `python-hydra-yaml` extension in VS Code
2. Configure the extension to point to your Hydra configuration directory
3. Open any YAML file in that directory to activate the language features

## 🔧 Development

```bash
# Clone and setup development environment
git clone https://github.com/your-repo/python-hydra-yaml.git
cd python-hydra-yaml/hydra-yaml-lsp

# Install dependencies and set up virtual environment
make venv

# Run all tests
make test

# Run type checking
make type

# Run all checks (tests and type checking)
make run
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.