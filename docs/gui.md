# Desktop GUI

organize now includes a cross-platform desktop GUI application for easier use of the file organization tool.

## Features

- Modern, user-friendly interface with sidebar navigation
- Built-in YAML editor for configuration
- One-click simulate and run operations
- Customizable settings: working directory, tags, skip-tags
- Real-time output logging with manual/auto save to file
- File dialogs for loading/saving configs and logs
- Cross-platform compatibility (Windows, macOS, Linux)
- Implements core CLI functionalities: config management, validation, execution

## Installation and Launch

After installing organize-tool:

```bash
organize-gui
```

Or from Python:

```python
from organize.gui import main
main()
```

## Usage

1. **Configuration**: Edit your rules, filters, actions in the YAML editor.
2. **Settings**: Set working directory and tags for selective rule execution.
3. **Actions**:
   - **New/Load/Save**: Manage config files.
   - **Check**: Validate YAML config.
   - **Simulate**: Preview changes without modifying files.
   - **Run**: Execute the organization (with confirmation).
   - **Save Logs**: Manually or auto-save output logs to file (after runs).
4. **Output**: View results in the console pane.

The GUI wraps the core library functions for Config loading, validation, and execution, supporting all filters and actions defined in the CLI.

## Customization

- Preferences can be set via the settings panel.
- Future extensions can include visual rule builders for filters/actions.

## Compatibility

Tested on major OS:
- Windows
- macOS
- Linux

Requires Python 3.9+ with Tkinter (standard library).

## User Guide

For detailed examples of configs, refer to [Rules](rules.md), [Filters](filters.md), [Actions](actions.md).

The GUI ensures safe simulation before any file changes, maintaining the safety features of organize.