import subprocess
import sys
from importlib.metadata import distribution

import requests
import rich
import typer
from packaging.version import Version
from rich.console import Console

import codegen

from .updater import UpdateManager

console = Console()


def fetch_pypi_releases(package: str) -> list[str]:
    response = requests.get(f"https://pypi.org/pypi/{package}/json")
    response.raise_for_status()
    return response.json()["releases"].keys()


def filter_versions(versions: list[Version], current_version: Version, num_prev_minor_version: int = 1) -> list[Version]:
    descending_minor_versions = [v_tuple for v_tuple in sorted(set(v.release[:2] for v in versions), reverse=True) if v_tuple < current_version.release[:2]]
    try:
        compare_tuple = descending_minor_versions[:num_prev_minor_version][-1] + (0,)
    except IndexError:
        compare_tuple = (current_version.major, current_version.minor, 0)

    return [v for v in versions if (v.major, v.minor, v.micro) >= compare_tuple]  # v.release will only show major,minor if micro doesn't exist.


def install_package(package: str, *args: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, *args])


def update(
    list_: bool = typer.Option(False, "--list", "-l", help="List all supported versions"),
    version: str | None = typer.Option(None, "--version", "-v", help="Update to a specific version"),
    check: bool = typer.Option(False, "--check", help="Check for available updates without installing"),
    legacy: bool = typer.Option(False, "--legacy", help="Use legacy update method (simple pip upgrade)"),
):
    """Update Codegen CLI to the latest or specified version.

    Examples:
        codegen update                    # Update to latest version
        codegen update --check            # Check for updates
        codegen update --version 1.2.3    # Update to specific version
    """
    # Handle legacy mode
    if legacy:
        _legacy_update(list_, version)
        return

    # Use new update manager
    manager = UpdateManager()

    # Handle different actions
    if check or list_:
        result = manager.check_for_updates(force=True)

        if result.update_available:
            console.print(f"\n[cyan]Update available: {result.current_version} → {result.latest_version}[/cyan]")
            console.print("[dim]Run 'codegen update' to upgrade[/dim]\n")
        else:
            console.print("[green]You're on the latest version![/green]")

        if list_ and result.versions:
            console.print("\n[bold]Available versions:[/bold]")
            for ver_info in result.versions[:10]:
                marker = " (current)" if ver_info.version == result.current_version else ""
                console.print(f"  {ver_info.version}{marker}")
    else:
        # Perform update
        if not manager.perform_update(target_version=version):
            raise typer.Exit(1)


def _legacy_update(list_: bool, version: str | None):
    """Legacy update method using simple pip upgrade."""
    package_name = codegen.__package__ or "codegen"
    package_info = distribution(package_name)
    current_version = Version(package_info.version)

    if list_:
        releases = fetch_pypi_releases(package_info.name)
        filtered_releases = filter_versions([Version(r) for r in releases], current_version, num_prev_minor_version=2)
        for release in filtered_releases:
            if release.release == current_version.release:
                rich.print(f"[bold]{release}[/bold] (current)")
            else:
                rich.print(release)
    elif version:
        install_package(f"{package_info.name}=={version}")
    else:
        # Update to latest version
        install_package(package_info.name, "--upgrade")
