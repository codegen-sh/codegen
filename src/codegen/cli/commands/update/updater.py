"""Simplified self-update system for the Codegen CLI."""

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional

import requests
from packaging.version import Version
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Update configuration
UPDATE_CHECK_FILE = Path.home() / ".codegen" / "update_check.json"
UPDATE_CHECK_INTERVAL = timedelta(hours=12)  # Check for updates once per day


class InstallMethod(Enum):
    """Installation methods for the CLI."""

    PIP = "pip"
    PIPX = "pipx"
    UV_TOOL = "uv_tool"
    HOMEBREW = "homebrew"
    GITHUB_RELEASE = "github"
    DEVELOPMENT = "development"
    UNKNOWN = "unknown"


@dataclass
class VersionInfo:
    """Information about a version."""

    version: Version
    release_date: datetime
    download_url: Optional[str] = None
    release_notes: Optional[str] = None
    size: Optional[int] = None


@dataclass
class UpdateCheckResult:
    """Result of checking for updates."""

    current_version: Version
    latest_version: Optional[Version] = None
    update_available: bool = False
    versions: List[VersionInfo] = None
    last_check: Optional[datetime] = None


class UpdateManager:
    """Manages self-updates for the CLI."""

    def __init__(self, package_name: str = "codegen"):
        self.package_name = package_name
        self.console = console
        self.install_method = self._detect_install_method()

    def _detect_install_method(self) -> InstallMethod:
        """Detect how the CLI was installed."""
        # Check for UV tool FIRST (before development check)
        # UV tools are installed in ~/.local/share/uv/tools/
        if ".local/share/uv/tools/" in sys.executable:
            return InstallMethod.UV_TOOL

        # Also check if the codegen command is in the UV managed bin directory
        try:
            import shutil

            codegen_path = shutil.which("codegen")
            if codegen_path and ".local/bin/codegen" in codegen_path:
                # Check if this links to a UV tool installation
                real_path = os.path.realpath(codegen_path)
                if ".local/share/uv/tools/" in real_path:
                    return InstallMethod.UV_TOOL
        except Exception:
            pass

        # Check for pipx
        if "pipx" in sys.executable or os.environ.get("PIPX_HOME"):
            return InstallMethod.PIPX

        # Check for Homebrew
        if platform.system() == "Darwin" and "/homebrew/" in sys.executable:
            return InstallMethod.HOMEBREW

        # Check if running from development environment
        # This check should come AFTER UV tool check since UV tool installations
        # may have direct_url.json files
        if "site-packages" not in sys.executable and "dist-packages" not in sys.executable:
            # Check if we're in an editable install
            try:
                import importlib.metadata

                dist = importlib.metadata.distribution(self.package_name)
                if dist.read_text("direct_url.json"):
                    return InstallMethod.DEVELOPMENT
            except Exception:
                pass

        # Check for pip
        if "site-packages" in sys.executable or "dist-packages" in sys.executable:
            return InstallMethod.PIP

        return InstallMethod.UNKNOWN

    def check_for_updates(self, force: bool = False) -> UpdateCheckResult:
        """Check for available updates."""
        # Load last check time
        last_check = self._load_last_check_time()

        # Skip check if recently checked (unless forced)
        if not force and last_check:
            if datetime.now() - last_check < UPDATE_CHECK_INTERVAL:
                return UpdateCheckResult(current_version=self._get_current_version(), last_check=last_check)

        current_version = self._get_current_version()

        try:
            # Fetch available versions
            versions = self._fetch_available_versions()

            # Find latest stable version
            latest = self._find_latest_version(versions)

            # Save check time
            self._save_last_check_time()

            return UpdateCheckResult(
                current_version=current_version,
                latest_version=latest.version if latest else None,
                update_available=latest and latest.version > current_version,
                versions=versions,
                last_check=datetime.now(),
            )
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not check for updates: {e}[/yellow]")
            return UpdateCheckResult(current_version=current_version)

    def _get_current_version(self) -> Version:
        """Get the current installed version."""
        import importlib.metadata

        dist = importlib.metadata.distribution(self.package_name)
        return Version(dist.version)

    def _fetch_available_versions(self) -> List[VersionInfo]:
        """Fetch available versions from PyPI."""
        versions = []

        # Fetch from PyPI
        try:
            response = requests.get(f"https://pypi.org/pypi/{self.package_name}/json", timeout=10)
            response.raise_for_status()
            data = response.json()

            for version_str, releases in data["releases"].items():
                try:
                    version = Version(version_str)

                    # Skip pre-releases
                    if version.is_prerelease:
                        continue

                    # Get release info
                    release_date = None
                    if releases:
                        upload_time = releases[0].get("upload_time_iso_8601")
                        if upload_time:
                            release_date = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))

                    versions.append(
                        VersionInfo(
                            version=version,
                            release_date=release_date or datetime.now(),
                            download_url=f"https://pypi.org/project/{self.package_name}/{version}/",
                        )
                    )
                except Exception:
                    continue  # Skip invalid versions
        except Exception as e:
            self.console.print(f"[yellow]Could not fetch PyPI versions: {e}[/yellow]")

        return sorted(versions, key=lambda v: v.version, reverse=True)

    def _find_latest_version(self, versions: List[VersionInfo]) -> Optional[VersionInfo]:
        """Find the latest stable version."""
        for version_info in versions:
            # Return the first (highest) version since list is sorted
            return version_info
        return None

    def _load_last_check_time(self) -> Optional[datetime]:
        """Load the last update check time."""
        if UPDATE_CHECK_FILE.exists():
            try:
                with open(UPDATE_CHECK_FILE) as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data.get("last_check"))
            except Exception:
                pass
        return None

    def _save_last_check_time(self) -> None:
        """Save the last update check time."""
        UPDATE_CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(UPDATE_CHECK_FILE, "w") as f:
            json.dump({"last_check": datetime.now().isoformat()}, f)

    def perform_update(self, target_version: Optional[str] = None, dry_run: bool = False, skip_confirmation: bool = False) -> bool:
        """Perform the update to a specific version or latest."""
        current_version = self._get_current_version()

        # Determine target version
        if target_version:
            try:
                target = Version(target_version)
            except Exception:
                self.console.print(f"[red]Invalid version: {target_version}[/red]")
                return False
        else:
            # Get latest stable version
            check_result = self.check_for_updates(force=True)
            if not check_result.update_available:
                self.console.print("[green]Already on the latest version![/green]")
                return True
            target = check_result.latest_version

        if target <= current_version:
            self.console.print(f"[yellow]Target version {target} is not newer than current {current_version}[/yellow]")
            return False

        # Show update plan
        self._show_update_plan(current_version, target, dry_run)

        if dry_run:
            return True

        # Confirm update (skip if already confirmed)
        if not skip_confirmation and not self._confirm_update():
            self.console.print("[yellow]Update cancelled[/yellow]")
            return False

        # Run pre-update hooks
        if not self._run_pre_update_hooks(current_version, target):
            self.console.print("[red]Pre-update checks failed[/red]")
            return False

        # Perform the update based on installation method
        success = self._perform_update_for_method(target)

        if success:
            # Run post-update hooks
            self._run_post_update_hooks(current_version, target)

            self.console.print(f"[green]✅ Successfully updated from {current_version} to {target}![/green]")
            self.console.print("\n[cyan]Please restart your terminal or run:[/cyan]")
            self.console.print("[bold]hash -r[/bold]  # For bash/zsh")
            self.console.print("[bold]rehash[/bold]   # For zsh")
        else:
            self.console.print("[red]Update failed.[/red]")

        return success

    def _show_update_plan(self, current: Version, target: Version, dry_run: bool) -> None:
        """Show the update plan."""
        panel_content = f"""
[cyan]Current Version:[/cyan] {current}
[cyan]Target Version:[/cyan]  {target}
[cyan]Install Method:[/cyan]  {self.install_method.value}
[cyan]Dry Run:[/cyan]        {dry_run}
"""

        self.console.print(Panel(panel_content.strip(), title="Update Plan", border_style="blue"))

    def _confirm_update(self) -> bool:
        """Confirm the update with the user."""
        from rich.prompt import Confirm

        return Confirm.ask("Do you want to proceed with the update?", default=True)

    def _run_pre_update_hooks(self, current: Version, target: Version) -> bool:
        """Run pre-update hooks."""
        # Check for breaking changes
        if target.major > current.major:
            self.console.print("[yellow]⚠️  Major version update detected - breaking changes possible[/yellow]")

        # No migrations needed for now
        return True

    def _run_post_update_hooks(self, previous: Version, current: Version) -> None:
        """Run post-update hooks."""
        # Show post-update tips
        if current.major > previous.major:
            self.console.print("\n[cyan]📚 Major version update completed![/cyan]")
            self.console.print("[dim]Check the changelog for breaking changes and new features.[/dim]")

    def _perform_update_for_method(self, target: Version) -> bool:
        """Perform update based on installation method."""
        if self.install_method == InstallMethod.PIP:
            return self._update_via_pip(target)
        elif self.install_method == InstallMethod.PIPX:
            return self._update_via_pipx(target)
        elif self.install_method == InstallMethod.UV_TOOL:
            return self._update_via_uv_tool(target)
        elif self.install_method == InstallMethod.HOMEBREW:
            return self._update_via_homebrew(target)
        elif self.install_method == InstallMethod.DEVELOPMENT:
            self.console.print("[yellow]Development installation detected - please update via git[/yellow]")
            return False
        else:
            self.console.print("[yellow]Unknown installation method - trying pip[/yellow]")
            return self._update_via_pip(target)

    def _update_via_pip(self, target: Version) -> bool:
        """Update using pip."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(f"Updating via pip to {target}...", total=None)

                subprocess.check_call([sys.executable, "-m", "pip", "install", f"{self.package_name}=={target}", "--upgrade"])
            return True
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]pip update failed: {e}[/red]")
            return False

    def _update_via_pipx(self, target: Version) -> bool:
        """Update using pipx."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(f"Updating via pipx to {target}...", total=None)

                subprocess.check_call(["pipx", "upgrade", self.package_name, "--pip-args", f"{self.package_name}=={target}"])
            return True
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]pipx update failed: {e}[/red]")
            return False

    def _update_via_uv_tool(self, target: Version) -> bool:
        """Update using uv tool."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(f"Updating via uv tool to {target}...", total=None)

                # UV tool requires different syntax: uv tool install --upgrade package==version
                subprocess.check_call(["uv", "tool", "install", "--upgrade", f"{self.package_name}=={target}"])
            return True
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]uv tool update failed: {e}[/red]")
            self.console.print("[yellow]You may need to manually update using:[/yellow]")
            self.console.print(f"[bold]uv tool install --upgrade {self.package_name}=={target}[/bold]")
            return False

    def _update_via_homebrew(self, target: Version) -> bool:
        """Update using Homebrew."""
        self.console.print("[yellow]Homebrew update not yet implemented - please use 'brew upgrade codegen'[/yellow]")
        return False


def check_for_updates_on_startup() -> None:
    """Check for updates on CLI startup with blocking prompt."""
    try:
        # Only check if we haven't checked recently
        manager = UpdateManager()
        result = manager.check_for_updates(force=True)

        if result.update_available:
            console.print(f"\n[cyan]ℹ️  A new version of Codegen CLI is available: {result.current_version} → {result.latest_version}[/cyan]")

            if manager.perform_update():
                console.print("\n[green]✓ Update completed successfully![/green]")
                console.print("[yellow]Please restart your terminal or run a new codegen command to use the updated version.[/yellow]\n")
                # Exit after successful update
                sys.exit(0)
            else:
                console.print("\n[red]Update failed. Please try running 'codegen update' manually.[/red]\n")

    except Exception:
        # Silently ignore update check failures on startup
        pass
