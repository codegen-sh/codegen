import json
import os
import shutil
import subprocess
import uuid
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from py_mini_racer import MiniRacer
from py_mini_racer._objects import JSMappedObject
from py_mini_racer._types import JSEvalException

from codegen.sdk.core.external.language_engine import LanguageEngine
from codegen.sdk.typescript.external.mega_racer import MegaRacer
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.core.external.dependency_manager import DependencyManager
    from codegen.sdk.core.interfaces.editable import Editable


logger = get_logger(__name__)


class TypescriptEngine(LanguageEngine):
    dependency_manager: "DependencyManager | None"

    def __init__(self, repo_path: str, base_path: str | None = None, dependency_manager: "DependencyManager | None" = None):
        super().__init__(repo_path, base_path)
        self.dependency_manager = dependency_manager

    @abstractmethod
    def _start(self):
        # If a dependency manager is provided, make sure it is ready
        if self.dependency_manager:
            logger.info(f"TypescriptEngine: Waiting for {self.dependency_manager.__class__.__name__} to be ready...")
            self.dependency_manager.wait_until_ready(ignore_error=True)
        # Start the engine
        super()._start()


class V8TypescriptEngine(TypescriptEngine):
    """Typescript-compiler based language engine using MiniRacer's V8-based JS engine.

    More experimental approach to type inference, but is faster and more flexible.

    Attributes:
        hard_memory_limit (int): Maximum memory limit in bytes before V8 will force garbage collection
        soft_memory_limit (int): Memory threshold in bytes that triggers garbage collection
    """

    hard_memory_limit: int
    soft_memory_limit: int
    ctx: MiniRacer | None
    mr_type_script_analyzer: JSMappedObject | None

    def __init__(
        self,
        repo_path: str,
        base_path: str | None = None,
        dependency_manager: "DependencyManager | None" = None,
        hard_memory_limit: int = 1024 * 1024 * 1024 * 16,
        soft_memory_limit: int = 1024 * 1024 * 1024 * 8,
    ):
        super().__init__(repo_path, base_path, dependency_manager)
        logger.info(f"Initializing V8TypescriptEngine with hard_memory_limit={hard_memory_limit} and soft_memory_limit={soft_memory_limit}")
        self.hard_memory_limit: int = hard_memory_limit
        self.soft_memory_limit: int = soft_memory_limit
        self.ctx: MiniRacer | None = None
        self.mr_type_script_analyzer: JSMappedObject | None = None
        # Get the path to the current file
        self.current_file_path: str = os.path.abspath(__file__)
        # Get the path of the language engine
        self.engine_path: str = os.path.join(os.path.dirname(self.current_file_path), "typescript_analyzer", "dist", "index.js")
        if not os.path.exists(self.engine_path):
            msg = f"Typescript analyzer engine not found at {self.engine_path}"
            raise FileNotFoundError(msg)
        self.engine_source: str = open(self.engine_path).read()
        self._patch_engine_source()

    def _start(self):
        try:
            logger.info("Starting V8TypescriptEngine")
            super()._start()
            # Create the MiniRacer/MegaRacer context
            self.ctx = MegaRacer()  # MegaRacer is a patch on MiniRacer that allows for more memory
            # Set to 16GB
            self.ctx.set_hard_memory_limit(self.hard_memory_limit)
            self.ctx.set_soft_memory_limit(self.soft_memory_limit)

            # Load the engine
            logger.info(f"Loading engine source with {len(self.engine_source)} bytes")
            self.ctx.eval(self.engine_source)

            # Set up proxy file system
            logger.info("Setting up proxy file system")
            self.ctx.eval("var interop_fs = new ProxyFileSystem();")
            self.ctx.eval("var fs_files = {};")
            fs_files = self.ctx.eval("fs_files")
            self._populate_fs_files(fs_files)
            self.ctx.eval("fs_file_map = new Map(Object.entries(fs_files));")
            self.ctx.eval("interop_fs.setFiles(fs_file_map);")

            # Set up the analyzer
            logger.info(f"Setting up analyzer with path {self.full_path}")
            self.ctx.eval(f"const type_script_analyzer = new TypeScriptAnalyzer('{self.full_path}', interop_fs);")
            self.mr_type_script_analyzer = self.ctx.eval("type_script_analyzer")

            # Finalize
            logger.info("Finalizing V8TypescriptEngine")
            self.is_ready = True
        except Exception as e:
            self._error = e
            logger.error(f"Error starting V8TypescriptEngine: {e}", exc_info=True)

    def _populate_fs_files(self, fs_files: dict):
        for root, _, files in os.walk(self.full_path):
            for filename in files:
                file_path = Path(root) / filename
                s_fp = str(file_path)

                # Only process JS/TS related files
                if not s_fp.endswith((".ts", ".tsx", ".js", ".jsx", ".json", ".d.ts")):
                    continue

                try:
                    with open(file_path, encoding="utf-8") as f:
                        if "node_modules" in s_fp:
                            if not s_fp.endswith(".json") and not s_fp.endswith(".d.ts"):
                                continue
                        content = f.read()
                        fs_files[str(file_path)] = content
                except (UnicodeDecodeError, OSError):
                    # Skip files that can't be read as text
                    continue

    def _patch_engine_source(self):
        """MiniRacer does not support require and export, so we need to patch the engine source to remove them."""
        logger.info("Patching engine source to remove require and export")
        patch_map = {
            "var require$$1 = require('fs');": "",
            "var require$$2 = require('path');": "",
            "var require$$3 = require('os');": "",
            "var require$$6 = require('inspector');": "",
            "exports.ProxyFileSystem = ProxyFileSystem;": "",
            "exports.TypeScriptAnalyzer = TypeScriptAnalyzer;": "",
        }
        for old, new in patch_map.items():
            self.engine_source = self.engine_source.replace(old, new)

    def get_return_type(self, node: "Editable") -> str | None:
        file_path = os.path.join(self.repo_path, node.filepath)
        try:
            return self.ctx.eval(f"type_script_analyzer.getFunctionAtPosition('{file_path}', {node.start_byte})")
        except JSEvalException as e:
            return None


class NodeTypescriptEngine(TypescriptEngine):
    """Typescript-compiler based language engine using NodeJS and the TypeScript compiler.

    More mature approach to type inference, but is slower and less flexible.

    Attributes:
        type_data (dict | None): Type data for the codebase
    """

    type_data: dict | None

    def __init__(self, repo_path: str, base_path: str | None = None, dependency_manager: "DependencyManager | None" = None):
        super().__init__(repo_path, base_path, dependency_manager)
        logger.info("Initializing NodeTypescriptEngine")
        self.type_data: dict | None = None

        # Get the path to the current file
        self.current_file_path: str = os.path.abspath(__file__)
        # Ensure NodeJS and npm are installed
        if not shutil.which("node") or not shutil.which("npm"):
            msg = "NodeJS or npm is not installed"
            raise RuntimeError(msg)

        # Get the path to the typescript analyzer
        self.analyzer_path: str = os.path.join(os.path.dirname(self.current_file_path), "typescript_analyzer")
        self.analyzer_entry: str = os.path.join(self.analyzer_path, "src", "run_full.ts")
        if not os.path.exists(self.analyzer_path):
            msg = f"Typescript analyzer not found at {self.analyzer_path}"
            raise FileNotFoundError(msg)

    def _start(self):
        try:
            logger.info("Starting NodeTypescriptEngine")
            super()._start()
            # NPM Install
            try:
                logger.info("Installing typescript analyzer dependencies")
                subprocess.run(["npm", "install"], cwd=self.analyzer_path, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.exception(f"NPM FAIL: npm install failed with exit code {e.returncode}")
                logger.exception(f"NPM FAIL stdout: {e.stdout}")
                logger.exception(f"NPM FAIL stderr: {e.stderr}")
                raise

            # Create a temporary output file with a random name
            output_file_path: str = f"/tmp/ts_analyzer_output_{uuid.uuid4()}.json"
            try:
                # Run the analyzer
                try:
                    # Create custom flags for node
                    node_environ = {**os.environ, "NODE_OPTIONS": "--max_old_space_size=8192"}

                    # Run the analyzer
                    logger.info(f"Running analyzer with project path {self.full_path} and output file {output_file_path}")
                    subprocess.run(
                        ["node", "--loader", "ts-node/esm", self.analyzer_entry, "--project", self.full_path, "--output", output_file_path],
                        cwd=self.analyzer_path,
                        check=True,
                        capture_output=True,
                        text=True,
                        env=node_environ,
                    )
                except subprocess.CalledProcessError as e:
                    logger.exception(f"ANALYZER FAIL: analyzer failed with exit code {e.returncode}")
                    logger.exception(f"ANALYZER FAIL stdout: {e.stdout}")
                    logger.exception(f"ANALYZER FAIL stderr: {e.stderr}")
                    raise

                # Load the type data
                self.type_data = json.load(open(output_file_path))
            finally:
                # Clean up the output file
                if os.path.exists(output_file_path):
                    os.remove(output_file_path)

            # Finalize
            logger.info("Finalizing NodeTypescriptEngine")
            self.is_ready = True
        except Exception as e:
            self._error = e
            logger.error(f"Error starting NodeTypescriptEngine: {e}", exc_info=True)

    def get_return_type(self, node: "Editable") -> str | None:
        file_path: str = os.path.join(self.repo_path, node.filepath)
        if not self.type_data:
            return None
        codebase_data: dict = self.type_data.get("files", {})
        file_data: dict = codebase_data.get(file_path, {})
        functions_data: dict = file_data.get("functions", {})
        function_data: dict = functions_data.get(node.name, {})
        return function_data.get("returnType", None)
