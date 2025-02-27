import concurrent.futures
import json
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from enum import Enum

import pyjson5
import requests

from codegen.sdk.core.external.dependency_manager import DependencyManager
from codegen.sdk.utils import shadow_files
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class InstallerType(Enum):
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    UNKNOWN = "unknown"


@dataclass
class PackageJsonData:
    dependencies: dict[str, str]
    dev_dependencies: dict[str, str]
    package_data: dict


class TypescriptDependencyManager(DependencyManager):
    should_install_dependencies: bool
    installer_type: InstallerType
    package_json_data: dict[str, PackageJsonData]
    base_package_json_data: PackageJsonData | None

    """Handles dependency management for Typescript projects. Uses npm, yarn, or pnpm if applicable."""

    def __init__(self, repo_path: str, base_path: str | None = None, should_install_dependencies: bool = True, force_installer: str | None = None):
        super().__init__(repo_path, base_path)
        logger.info(f"Initializing TypescriptDependencyManager with should_install_dependencies={should_install_dependencies}")
        # Ensure that node, npm, yarn, and pnpm are installed
        if not shutil.which("node"):
            msg = "NodeJS is not installed"
            raise RuntimeError(msg)
        if not shutil.which("corepack"):
            msg = "corepack is not installed"
            raise RuntimeError(msg)
        if not shutil.which("npm"):
            msg = "npm is not installed"
            raise RuntimeError(msg)
        if not shutil.which("yarn"):
            msg = "yarn is not installed"
            raise RuntimeError(msg)
        if not shutil.which("pnpm"):
            msg = "pnpm is not installed"
            raise RuntimeError(msg)

        self.should_install_dependencies = should_install_dependencies
        # Detect the installer type
        if force_installer:
            self.installer_type = InstallerType(force_installer)
        else:
            self.installer_type = self._detect_installer_type()

        logger.info(f"Detected installer type: {self.installer_type}")

        # List of package.json files with their parsed data
        self.package_json_data: dict[str, PackageJsonData] = {}
        self.base_package_json_data: PackageJsonData | None = None

    def _detect_installer_type(self) -> InstallerType:
        if os.path.exists(os.path.join(self.full_path, "yarn.lock")):
            return InstallerType.YARN
        elif os.path.exists(os.path.join(self.full_path, "package-lock.json")):
            return InstallerType.NPM
        elif os.path.exists(os.path.join(self.full_path, "pnpm-lock.yaml")):
            return InstallerType.PNPM
        else:
            logger.warning("Could not detect installer type. Defaulting to NPM!")
            return InstallerType.NPM
            # return InstallerType.UNKNOWN

    @staticmethod
    def _check_package_exists(package_name: str) -> bool:
        """Check if a package exists on the npm registry."""
        url = f"https://registry.npmjs.org/{package_name}"
        try:
            response = requests.head(url)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @classmethod
    def _validate_dependencies(cls, deps: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
        """Validate a dictionary of dependencies against npm registry."""
        valid_deps = {}
        invalid_deps = {}

        # Use ThreadPoolExecutor for concurrent validation
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_package = {executor.submit(cls._check_package_exists, package): (package, version) for package, version in deps.items()}

            for future in concurrent.futures.as_completed(future_to_package):
                package, version = future_to_package[future]
                try:
                    exists = future.result()
                    # Hack to fix github packages
                    if "github" in version:
                        version = version.split("#")[0]
                    if exists:
                        valid_deps[package] = version
                    else:
                        invalid_deps[package] = version
                except Exception as e:
                    logger.exception(f"Error checking package {package}: {e}")

        return valid_deps, invalid_deps

    def parse_dependencies(self):
        # Clear the package_json_data
        self.package_json_data.clear()

        # Walk through directory tree
        for current_dir, subdirs, files in os.walk(self.full_path):
            # Skip node_modules directories
            if "node_modules" in current_dir:
                continue

            # Check if package.json exists in current directory
            if "package.json" in files:
                # Convert to absolute path and append to results
                package_json_path = os.path.join(current_dir, "package.json")

                # Parse the package.json file
                try:
                    # Read package.json
                    with open(package_json_path) as f:
                        package_data = pyjson5.load(f)

                    # Get dependencies and devDependencies
                    dependencies = package_data.get("dependencies", {})
                    dev_dependencies = package_data.get("devDependencies", {})

                    self.package_json_data[package_json_path] = PackageJsonData(dependencies, dev_dependencies, package_data)

                except FileNotFoundError:
                    logger.exception(f"Could not find package.json at {package_json_path}")
                except ValueError:
                    logger.exception(f"Invalid json in package.json at {package_json_path}")
                except Exception as e:
                    raise e

        # Set the base package.json data
        base_package_json_path = os.path.join(self.full_path, "package.json")
        self.base_package_json_data = self.package_json_data.get(base_package_json_path, None)

    def _install_dependencies_npm(self):
        logger.info("Installing dependencies with NPM")
        # Shadow package-lock.json, if it exists
        files_to_shadow = []
        # Check if package-lock.json exists.
        if os.path.exists(os.path.join(self.full_path, "package-lock.json")):
            files_to_shadow.append(os.path.join(self.full_path, "package-lock.json"))

        # Shadow the files
        with shadow_files(files_to_shadow):
            # Remove the original package-lock.json
            for file_path in files_to_shadow:
                os.remove(file_path)

            # Print the node version
            logger.info(f"Node version: {subprocess.check_output(['node', '--version'], cwd=self.full_path, text=True).strip()}")

            # Print the npm version
            logger.info(f"NPM version: {subprocess.check_output(['npm', '--version'], cwd=self.full_path, text=True).strip()}")

            # NPM Install
            try:
                logger.info(f"Running npm install with cwd {self.full_path}")
                subprocess.run(["npm", "install"], cwd=self.full_path, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.exception(f"NPM FAIL: npm install failed with exit code {e.returncode}")
                logger.exception(f"NPM FAIL stdout: {e.stdout}")
                logger.exception(f"NPM FAIL stderr: {e.stderr}")
                raise

    def _install_dependencies_yarn(self):
        logger.info("Installing dependencies with Yarn")
        # Shadow yarn.lock, yarn.config.cjs, and .yarnrc.yml, if they exist
        files_to_shadow = []
        # Check if yarn.lock exists.
        if os.path.exists(os.path.join(self.full_path, "yarn.lock")):
            files_to_shadow.append(os.path.join(self.full_path, "yarn.lock"))
        # Check if yarn.config.cjs exists. This fixes constraints
        if os.path.exists(os.path.join(self.full_path, "yarn.config.cjs")):
            files_to_shadow.append(os.path.join(self.full_path, "yarn.config.cjs"))
        # Check if .yarnrc.yml exists. This fixes pre and post install scripts
        if os.path.exists(os.path.join(self.full_path, ".yarnrc.yml")):
            files_to_shadow.append(os.path.join(self.full_path, ".yarnrc.yml"))

        # Shadow the files
        with shadow_files(files_to_shadow):
            # If .yarnrc.yml exists, check if the yarnPath option is set and save it
            yarn_path = None
            if os.path.exists(os.path.join(self.full_path, ".yarnrc.yml")):
                # Grab the line with "yarnPath"
                with open(os.path.join(self.full_path, ".yarnrc.yml")) as f:
                    for line in f:
                        if "yarnPath" in line:
                            yarn_path = line.split(":")[1].strip()
                            break
            # Remove all the shadowed files
            for file_path in files_to_shadow:
                os.remove(file_path)

            try:
                # Disable PnP
                with open(os.path.join(self.full_path, ".yarnrc.yml"), "w") as f:
                    f.write("nodeLinker: node-modules\n")
                    if yarn_path:
                        f.write(f"yarnPath: {yarn_path}\n")

                # Print the node version
                logger.info(f"Node version: {subprocess.check_output(['node', '--version'], cwd=self.full_path, text=True).strip()}")

                # Print the yarn version
                logger.info(f"Yarn version: {subprocess.check_output(['yarn', '--version'], cwd=self.full_path, text=True).strip()}")

                # This fixes a bug where swapping yarn versions corrups the metadata and package caches,
                # causing all sorts of nasty issues
                yarn_temp_global_dir: str = f"/tmp/yarn_tmp_{uuid.uuid4()}"
                try:
                    # Yarn Install
                    try:
                        # Create custom flags for yarn
                        yarn_custom_flags = {
                            "YARN_ENABLE_IMMUTABLE_INSTALLS": "false",
                            "YARN_ENABLE_TELEMETRY": "false",
                            "YARN_ENABLE_GLOBAL_CACHE": "true",
                            "YARN_GLOBAL_FOLDER": yarn_temp_global_dir,
                        }
                        yarn_environ = {
                            **os.environ,
                            **yarn_custom_flags,
                        }

                        # Set up yarn
                        logger.info(f"Running yarn install with cwd {self.full_path} and yarn_custom_flags {yarn_custom_flags}")
                        subprocess.run(["corepack", "enable"], cwd=self.full_path, check=True, capture_output=True, text=True)
                        subprocess.run(["corepack", "prepare", "--activate"], cwd=self.full_path, check=True, capture_output=True, text=True)
                        subprocess.run(["yarn", "install"], cwd=self.full_path, check=True, capture_output=True, text=True, env=yarn_environ)
                    except subprocess.CalledProcessError as e:
                        logger.exception(f"Yarn FAIL: yarn install failed with exit code {e.returncode}")
                        logger.exception(f"Yarn FAIL stdout: {e.stdout}")
                        logger.exception(f"Yarn FAIL stderr: {e.stderr}")
                        raise
                finally:
                    # Clean up the temporary global directory
                    if os.path.exists(yarn_temp_global_dir):
                        shutil.rmtree(yarn_temp_global_dir)
            finally:
                # Check if the .yarnrc.yml file exists
                if os.path.exists(os.path.join(self.full_path, ".yarnrc.yml")):
                    # Delete the .yarnrc.yml file
                    os.remove(os.path.join(self.full_path, ".yarnrc.yml"))

    def _install_dependencies_pnpm(self):
        logger.info("Installing dependencies with PNPM")
        # Shadow pnpm-lock.yaml, if it exists
        files_to_shadow = []
        if os.path.exists(os.path.join(self.full_path, "pnpm-lock.yaml")):
            files_to_shadow.append(os.path.join(self.full_path, "pnpm-lock.yaml"))

        # Shadow the files
        with shadow_files(files_to_shadow):
            # Remove all the shadowed files
            for file_path in files_to_shadow:
                os.remove(file_path)

            # Print the node version
            logger.info(f"Node version: {subprocess.check_output(['node', '--version'], cwd=self.full_path, text=True).strip()}")

            # Print the pnpm version
            logger.info(f"PNPM version: {subprocess.check_output(['pnpm', '--version'], cwd=self.full_path, text=True).strip()}")

            # PNPM Install
            try:
                logger.info(f"Running pnpm install with cwd {self.full_path}")
                subprocess.run(["pnpm", "install"], cwd=self.full_path, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.exception(f"PNPM FAIL: pnpm install failed with exit code {e.returncode}")
                logger.exception(f"PNPM FAIL stdout: {e.stdout}")
                logger.exception(f"PNPM FAIL stderr: {e.stderr}")
                raise

    def _clean_package_json(self, package_json_path: str):
        # Get the package data
        data = self.package_json_data[package_json_path]

        # Get valid dependencies
        valid_deps, _ = self._validate_dependencies(data.dependencies)
        valid_dev_deps, _ = self._validate_dependencies(data.dev_dependencies)

        # Create a slimmed down package.json with only the valid dependencies
        clean_package_data = {}

        # Copy important fields
        clean_package_data["name"] = data.package_data.get("name", "unknown")
        clean_package_data["version"] = data.package_data.get("version", "v1.0.0")
        if "packageManager" in data.package_data:
            clean_package_data["packageManager"] = data.package_data["packageManager"]
        if "workspaces" in data.package_data:
            clean_package_data["workspaces"] = data.package_data["workspaces"]

        # Copy dependencies
        clean_package_data["dependencies"] = valid_deps
        clean_package_data["devDependencies"] = valid_dev_deps

        # Write the cleaned package.json
        with open(package_json_path, "w") as f:
            json_str = json.dumps(clean_package_data, indent=2)
            f.write(json_str)

    def install_dependencies(self, validate_dependencies: bool = True):
        if validate_dependencies:
            with shadow_files(list(self.package_json_data.keys())):
                logger.info(f"Cleaning package.json files: {list(self.package_json_data.keys())}")
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    executor.map(self._clean_package_json, self.package_json_data.keys())

                # Install dependencies, now that we have a valid package.json
                return self.install_dependencies(validate_dependencies=False)
        else:
            if self.installer_type == InstallerType.NPM:
                return self._install_dependencies_npm()
            elif self.installer_type == InstallerType.YARN:
                return self._install_dependencies_yarn()
            elif self.installer_type == InstallerType.PNPM:
                return self._install_dependencies_pnpm()
            else:
                logger.warning(f"Installer type {self.installer_type} not implemented")

    def remove_dependencies(self):
        # Delete node_modules folder if it exists
        node_modules_path = os.path.join(self.full_path, "node_modules")
        if os.path.exists(node_modules_path):
            shutil.rmtree(node_modules_path)

    def _start(self):
        try:
            logger.info(f"Starting TypescriptDependencyManager with should_install_dependencies={self.should_install_dependencies}")
            super()._start()
            # Remove dependencies if we are installing them
            if self.should_install_dependencies:
                logger.info("Removing existing dependencies")
                self.remove_dependencies()

            # Parse dependencies
            logger.info("Parsing dependencies")
            self.parse_dependencies()

            # Install dependencies if we are installing them
            if self.should_install_dependencies:
                logger.info("Installing dependencies")
                self.install_dependencies()

            # We are ready
            logger.info("Finalizing TypescriptDependencyManager")
            self.is_ready = True
        except Exception as e:
            self._error = e
            logger.error(f"Error starting TypescriptDependencyManager: {e}", exc_info=True)
