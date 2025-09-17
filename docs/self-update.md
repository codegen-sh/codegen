# Self-Update System for Codegen CLI

The Codegen CLI includes a simplified self-update system that allows users to easily update to the latest version.

## Features

### 🚀 Smart Update Detection
- Automatically detects installation method (pip, pipx, uv tool, homebrew, development)
- Checks for updates periodically (once per day by default)
- Shows update notifications when new versions are available
- Fetches stable releases from PyPI

### 🔄 Update Management
- Update to latest stable version
- Update to specific versions
- Dry-run mode to preview changes
- Legacy mode for simple pip upgrades

### 🛡️ Safety Features
- Pre-update validation checks
- Major version update warnings
- Post-update tips and guidance

### 📊 Version Information
- List available versions
- Check for updates without installing
- View current and latest versions

## Usage

### Basic Commands

```bash
# Update to latest stable version
codegen update

# Check for available updates without installing
codegen update --check

# List available versions
codegen update --list

# Show version history
codegen update --history
```

### Advanced Options

```bash
# Update to specific version
codegen update --version 1.2.3

# Preview update without making changes
codegen update --dry-run

# Force update check (bypass cache)
codegen update --force

# Use legacy pip upgrade method
codegen update --legacy
```

## Release Information

The update system fetches stable releases from PyPI. Pre-release versions are automatically filtered out to ensure stability. Only production-ready versions are shown and available for installation through the update command.

## Installation Methods

The update system automatically detects how Codegen was installed and uses the appropriate update method:

### pip Installation
```bash
pip install codegen
# Updates via: pip install --upgrade codegen
```

### pipx Installation
```bash
pipx install codegen
# Updates via: pipx upgrade codegen
```

### UV Tool Installation
```bash
uv tool install codegen
# Updates via: uv tool install --upgrade codegen
```

### Homebrew Installation (macOS)
```bash
brew install codegen
# Updates via: brew upgrade codegen
```

### Development Installation
For development/editable installs, the update system will notify you to update via git:
```bash
git pull origin main
pip install -e .
```

## Update Process

The update system performs a streamlined update process:

### How Updates Work

1. **Version Check**: Fetches available versions from PyPI
2. **Comparison**: Compares current version with available versions
3. **Confirmation**: Asks for user confirmation before proceeding
4. **Installation**: Uses the appropriate package manager to update
5. **Verification**: Displays success message and restart instructions

### Major Version Updates

When updating to a new major version:
- The system warns about potential breaking changes
- Post-update tips are displayed
- Users are encouraged to check the changelog

## Update Notifications

The CLI checks for updates periodically and shows notifications when new versions are available:

```
ℹ️  A new version of Codegen CLI is available: 1.2.3
Run 'codegen update' to upgrade
```

### Disable Update Checks

To disable automatic update checks, set the environment variable:

```bash
export CODEGEN_DISABLE_UPDATE_CHECK=1
```

## Downgrading

If an update causes issues, you can downgrade to a previous version:

```bash
# Downgrade to a specific version
codegen update --version 1.2.2

# Or use your package manager directly
pip install codegen==1.2.2
pipx install codegen==1.2.2 --force
uv tool install codegen==1.2.2 --upgrade
```

## Configuration

Update settings are stored in `~/.codegen/`:

- `update_check.json` - Last update check timestamp and cache

## Troubleshooting

### Update Fails

1. Try using the legacy update method:
   ```bash
   codegen update --legacy
   ```

2. Manually update via pip:
   ```bash
   pip install --upgrade codegen
   ```

3. Check installation method:
   ```bash
   which codegen
   pip show codegen
   ```

### Permission Errors

If you get permission errors, you may need to use sudo (not recommended) or update your user installation:

```bash
# For user installation
pip install --user --upgrade codegen

# For pipx
pipx upgrade codegen
```

### Downgrade Issues

If you need to downgrade:

1. Use the update command with a specific version:
   ```bash
   codegen update --version 1.2.2
   ```

2. Or manually install the desired version:
   ```bash
   pip install codegen==1.2.2
   pipx install codegen==1.2.2 --force
   uv tool install codegen==1.2.2 --upgrade
   ```

## Development

### Testing Updates

Test the update system in development:

```bash
# Check current version
codegen --version

# Test update check
codegen update --check --force

# Test dry-run update
codegen update --dry-run

# Test specific version
codegen update --version 1.2.3 --dry-run
```

### Adding New Features

To add new update features:

1. Modify `updater.py` for core functionality
2. Update command options in `main.py`
3. Add tests for new functionality

## API Reference

### UpdateManager Class

```python
from codegen.cli.commands.update import UpdateManager

manager = UpdateManager()

# Check for updates
result = manager.check_for_updates(force=True)

# Perform update
success = manager.perform_update(target_version="1.2.3", dry_run=False)

# Check installation method
print(manager.install_method)
```

### Installation Methods

```python
from codegen.cli.commands.update.updater import InstallMethod

methods = [
    InstallMethod.PIP,
    InstallMethod.PIPX,
    InstallMethod.UV_TOOL,
    InstallMethod.HOMEBREW,
    InstallMethod.DEVELOPMENT,
    InstallMethod.UNKNOWN
]
```

## Best Practices

1. **Regular Updates**: Keep your CLI updated for latest features and security fixes
2. **Check Changelog**: Review breaking changes before major version updates
3. **Test in Dev**: Test updates in development environment first
4. **Use Dry Run**: Preview updates with `--dry-run` before applying
5. **Report Issues**: Report update issues to help improve the system

## Security

- Updates are fetched over HTTPS from PyPI
- Package signatures are verified by pip/pipx/uv
- Pre-release versions are filtered out automatically
- Major version updates require confirmation

## Future Enhancements

- [ ] Automatic rollback on update failure
- [ ] Configuration migration system
- [ ] Release notes integration
- [ ] Beta and nightly release channels
- [ ] Binary distribution for faster updates
- [ ] Automatic security update installation
- [ ] Update progress with detailed logging
- [ ] Network proxy support
- [ ] Offline update packages
