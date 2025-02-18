import subprocess
import sys
from importlib.metadata import distribution

import requests
import rich
import rich_click as click
from packaging.version import Version

import codegen


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


@click.command(name="update")
@click.option(
    "--list",
    "-l",
    "list_",
    is_flag=True,
    help="List all supported versions of the codegen",
)
@click.option("--version", "-v", type=str, help="Update to a specific version of the codegen")
def update_command(list_: bool = False, version: str | None = None):
    """Update Codegen to the latest or specified version

    --list: List all supported versions of the codegen
    --version: Update to a specific version of the codegen
    """
    if list_ and version:
        msg = "Cannot specify both --list and --version"
        raise click.ClickException(msg)

    package_info = distribution(codegen.__package__)
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
