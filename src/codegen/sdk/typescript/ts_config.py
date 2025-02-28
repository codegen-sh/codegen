import os
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import pyjson5

from codegen.sdk.core.directory import Directory
from codegen.sdk.core.file import File
from codegen.shared.decorators.docs import ts_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.typescript.config_parser import TSConfigParser
    from codegen.sdk.typescript.file import TSFile

logger = get_logger(__name__)


@ts_apidoc
class TSConfig:
    """TypeScript configuration file specified in tsconfig.json, used for import resolution and computing dependencies.

    Attributes:
        config_file: The configuration file object representing the tsconfig.json file.
        config_parser: The parser used to interpret the TypeScript configuration.
        config: A dictionary containing the parsed configuration settings.
    """

    config_file: File
    config_parser: "TSConfigParser"
    config: dict

    # Base config values
    _base_config: "TSConfig | None" = None
    _base_url: str | None = None
    _out_dir: str | None = None
    _root_dir: str | None = None
    _root_dirs: list[str] = []
    _paths: dict[str, list[str]] = {}
    _references: list[tuple[str, Directory | File]] = []

    # Self config values
    _self_base_url: str | None = None
    _self_out_dir: str | None = None
    _self_root_dir: str | None = None
    _self_root_dirs: list[str] = []
    _self_paths: dict[str, list[str]] = {}
    _self_references: list[Directory | File] = []

    # Precomputed import aliases
    _computed_path_import_aliases: bool = False
    _path_import_aliases: dict[str, list[str]] = {}
    _reference_import_aliases: dict[str, list[str]] = {}
    # Optimization hack. If all the path alises start with `@` or `~`, then we can skip any path that doesn't start with `@` or `~`
    # when computing the import resolution.
    _import_optimization_enabled: bool = False

    def __init__(self, config_file: File, config_parser: "TSConfigParser"):
        self.config_file = config_file
        self.config_parser = config_parser
        # Try to parse the config file as JSON5. Fallback to empty dict if it fails.
        # We use json5 because it supports comments in the config file.
        try:
            self.config = pyjson5.loads(config_file.content)
        except pyjson5.Json5Exception:
            logger.exception(f"Failed to parse tsconfig.json file: {config_file.filepath}")
            self.config = {}

        # Precompute the base config, base url, paths, and references
        self._precompute_config_values()

    def __repr__(self):
        return f"TSConfig({self.config_file.filepath})"

    def _precompute_config_values(self):
        """Precomputes the base config, base url, paths, and references."""
        # Precompute the base config
        self._base_config = None
        extends = self.config.get("extends", None)
        if isinstance(extends, list):
            # TODO: Support multiple extends
            extends = extends[0]  # Grab the first config in the list
        base_config_path = self._parse_parent_config_path(extends)

        if base_config_path and base_config_path.exists():
            self._base_config = self.config_parser.get_config(base_config_path)

        # Precompute the base url
        self._base_url = None
        self._self_base_url = None
        if base_url := self.config.get("compilerOptions", {}).get("baseUrl", None):
            self._base_url = base_url
            self._self_base_url = base_url
        elif base_url := {} if self.base_config is None else self.base_config.base_url:
            self._base_url = base_url

        # Precompute the outDir
        self._out_dir = None
        self._self_out_dir = None
        if out_dir := self.config.get("compilerOptions", {}).get("outDir", None):
            self._out_dir = out_dir
            self._self_out_dir = out_dir
        elif out_dir := {} if self.base_config is None else self.base_config.out_dir:
            self._out_dir = out_dir

        # Precompute the rootDir
        self._root_dir = None
        self._self_root_dir = None
        if root_dir := self.config.get("compilerOptions", {}).get("rootDir", None):
            self._root_dir = root_dir
            self._self_root_dir = root_dir
        elif root_dir := {} if self.base_config is None else self.base_config.root_dir:
            self._root_dir = root_dir

        # Precompute the rootDirs
        self._root_dirs = []
        self._self_root_dirs = []
        if root_dirs := self.config.get("compilerOptions", {}).get("rootDirs", None):
            self._root_dirs = root_dirs
            self._self_root_dirs = root_dirs
        elif root_dirs := [] if self.base_config is None else self.base_config.root_dirs:
            self._root_dirs = root_dirs

        # Precompute the paths
        base_paths = {} if self.base_config is None else self.base_config.paths
        self_paths = self.config.get("compilerOptions", {}).get("paths", {})
        self._paths = {**base_paths, **self_paths}
        self._self_paths = self_paths

        # Precompute the references
        self_references = []
        references = self.config.get("references", None)
        if references is not None:
            for reference in references:
                if ref_path := reference.get("path", None):
                    abs_ref_path = str(self.config_file.ctx.to_relative(self._relative_to_absolute_directory_path(ref_path)))
                    if directory := self.config_file.ctx.get_directory(self.config_file.ctx.to_absolute(abs_ref_path)):
                        self_references.append((ref_path, directory))
                    elif ts_config := self.config_parser.get_config(abs_ref_path):
                        self_references.append((ref_path, ts_config.config_file))
                    elif file := self.config_file.ctx.get_file(abs_ref_path):
                        self_references.append((ref_path, file))
        self._references = [*self_references]  # MAYBE add base references here? This breaks the reference chain though.
        self._self_references = self_references

    def _precompute_import_aliases(self):
        """Precomputes the import aliases."""
        if self._computed_path_import_aliases:
            return

        # Force compute alias of the base config
        if self.base_config is not None:
            self.base_config._precompute_import_aliases()

        # Precompute the formatted paths based on compilerOptions/paths
        base_path_import_aliases = {} if self.base_config is None else self.base_config.path_import_aliases
        self_path_import_aliases = {}
        for pattern, relative_paths in self._self_paths.items():
            formatted_pattern = pattern.replace("*", "").rstrip("/").replace("//", "/")
            formatted_relative_paths = []
            for relative_path in relative_paths:
                cleaned_relative_path = relative_path.replace("*", "").rstrip("/").replace("//", "/")
                if self._self_base_url:
                    cleaned_relative_path = os.path.join(self._self_base_url, cleaned_relative_path)
                formatted_absolute_path = self._relative_to_absolute_directory_path(cleaned_relative_path)
                formatted_relative_path = str(self.config_file.ctx.to_relative(formatted_absolute_path))
                # Fix absolute path if its base
                if formatted_relative_path == ".":
                    formatted_relative_path = ""
                formatted_relative_paths.append(formatted_relative_path)
            self_path_import_aliases[formatted_pattern] = formatted_relative_paths
        self._path_import_aliases = {**base_path_import_aliases, **self_path_import_aliases}

        # Precompute the formatted paths based on references
        base_reference_import_aliases = {} if self.base_config is None else self.base_config.reference_import_aliases
        self_reference_import_aliases = {}
        # For each reference, try to grab its tsconfig.
        for ref_path, reference in self._self_references:
            # TODO: THIS ENTIRE PROCESS IS KINDA HACKY.
            # If the reference is a file, get its directory.
            if isinstance(reference, File):
                reference_dir = self.config_file.ctx.get_directory(os.path.dirname(reference.filepath))
            elif isinstance(reference, Directory):
                reference_dir = reference
            else:
                logger.warning(f"Unknown reference type during self_reference_import_aliases computation in _precompute_import_aliases: {type(reference)}")
                continue

            # With the directory, try to grab the next available file and get its tsconfig.
            if reference_dir and reference_dir.files(recursive=True):
                next_file: TSFile = reference_dir.files(recursive=True)[0]
            else:
                logger.warning(f"No next file found for reference during self_reference_import_aliases computation in _precompute_import_aliases: {reference.dirpath}")
                continue
            target_ts_config = next_file.ts_config
            if target_ts_config is None:
                logger.warning(f"No tsconfig found for reference during self_reference_import_aliases computation in _precompute_import_aliases: {reference.dirpath}")
                continue

            # With the tsconfig, grab its rootDirs and outDir
            target_root_dirs = target_ts_config.root_dirs if target_ts_config.root_dirs else ["."]
            target_out_dir = target_ts_config.out_dir

            # Calculate the formatted pattern and formatted relative paths
            formatted_relative_paths = [os.path.normpath(os.path.join(reference_dir.path, root_dir)) for root_dir in target_root_dirs]

            # Loop through each possible path part of the reference
            # For example, if the reference is "../../a/b/c" and the out dir is "dist"
            # then the possible reference aliases are:
            # - "a/b/c/dist"
            # - "b/c/dist"
            # - "c/dist"
            # (ignoring any .. segments)
            path_parts = [p for p in ref_path.split(os.path.sep) if p and not p.startswith("..")]
            for i in range(len(path_parts)):
                target_path = os.path.sep.join(path_parts[i:])
                if target_path:
                    formatted_target_path = os.path.normpath(os.path.join(target_path, target_out_dir) if target_out_dir else target_path)
                    self_reference_import_aliases[formatted_target_path] = formatted_relative_paths

        self._reference_import_aliases = {**base_reference_import_aliases, **self_reference_import_aliases}

        # Precompute _import_optimization_enabled
        self._import_optimization_enabled = all(k.startswith("@") or k.startswith("~") for k in list(self.path_import_aliases.keys()) + list(self.reference_import_aliases.keys()))

        # Mark that we've precomputed the import aliases
        self._computed_path_import_aliases = True

    def _parse_parent_config_path(self, config_filepath: str | None) -> Path | None:
        """Returns a TSConfig object from a file path."""
        if config_filepath is None:
            return None

        path = self._relative_to_absolute_directory_path(config_filepath)
        return Path(path if path.suffix == ".json" else f"{path}.json")

    def _relative_to_absolute_directory_path(self, relative_path: str) -> Path:
        """Helper to go from a relative module to an absolute one.
        Ex: "../pkg-common/" would be -> "src/dir/pkg-common/"
        """
        # TODO: This could also use its parent config to resolve the path
        relative = self.config_file.path.parent / relative_path.strip('"')
        return self.config_file.ctx.to_absolute(relative)

    def translate_import_path(self, import_path: str) -> str:
        """Translates an import path to an absolute path using the tsconfig paths.

        Takes an import path and translates it to an absolute path using the configured paths in the tsconfig file. If the import
        path matches a path alias, it will be resolved according to the tsconfig paths mapping.

        For example, converts `@abc/my/pkg/src` to `a/b/c/my/pkg/src` or however it's defined in the tsconfig.

        Args:
            import_path (str): The import path to translate.

        Returns:
            str: The translated absolute path. If no matching path alias is found, returns the original import path unchanged.
        """
        # Break out early if we can
        if self._import_optimization_enabled and not import_path.startswith("@") and not import_path.startswith("~"):
            return import_path

        # Step 1: Try to resolve with import_resolution_overrides
        if self.config_file.ctx.config.import_resolution_overrides:
            if path_check := TSConfig._find_matching_path(frozenset(self.config_file.ctx.config.import_resolution_overrides.keys()), import_path):
                to_base = self.config_file.ctx.config.import_resolution_overrides[path_check]

                # Get the remaining path after the matching prefix
                remaining_path = import_path[len(path_check) :].lstrip("/")

                # Join the path together
                import_path = os.path.join(to_base, remaining_path)

                return import_path

        # Step 2: Keep traveling down the parent config paths until we find a match a reference_import_aliases
        if path_check := TSConfig._find_matching_path(frozenset(self.reference_import_aliases.keys()), import_path):
            # TODO: This assumes that there is only one to_base path for the given from_base path
            to_base = self.reference_import_aliases[path_check][0]

            # Get the remaining path after the matching prefix
            remaining_path = import_path[len(path_check) :].lstrip("/")

            # Join the path together
            import_path = os.path.join(to_base, remaining_path)

            return import_path

        # Step 3: Keep traveling down the parent config paths until we find a match a path_import_aliases
        if path_check := TSConfig._find_matching_path(frozenset(self.path_import_aliases.keys()), import_path):
            # TODO: This assumes that there is only one to_base path for the given from_base path
            to_base = self.path_import_aliases[path_check][0]

            # Get the remaining path after the matching prefix
            remaining_path = import_path[len(path_check) :].lstrip("/")

            # Join the path together
            import_path = os.path.join(to_base, remaining_path)

            return import_path

        # Step 4: Try to resolve with base path for non-relative imports
        return self.resolve_base_url(import_path)

    def translate_absolute_path(self, absolute_path: str) -> str:
        """Translates an absolute path to an import path using the tsconfig paths.

        Takes an absolute path and translates it to an import path using the configured paths in the tsconfig file.

        For example, converts `a/b/c/my/pkg/src` to `@abc/my/pkg/src` or however it's defined in the tsconfig.

        Args:
            import_path (str): The absolute path to translate.

        Returns:
            str: The translated import path.
        """
        path_aliases = self._path_import_aliases
        for alias, paths in path_aliases.items():
            for path in paths:
                if absolute_path.startswith(path):
                    # Pick the first alias that matches
                    return absolute_path.replace(path, alias, 1)

        return absolute_path

    def resolve_base_url(self, import_path: str) -> str:
        """Resolves an import path with the base url.

        If a base url is not defined, try to resolve it with its base config.
        """
        # Do nothing if the import path is relative
        if import_path.startswith("."):
            return import_path

        # If the current config has a base url, use itq
        if self._self_base_url:
            if not import_path.startswith(self._self_base_url):
                import_path = os.path.join(self._self_base_url, import_path)
                import_path = str(self._relative_to_absolute_directory_path(import_path))
            return import_path
        # If there is a base config, try to resolve it with its base url
        elif self.base_config:
            return self.base_config.resolve_base_url(import_path)
        # Otherwise, do nothing
        else:
            return import_path

    @staticmethod
    @cache
    def _find_matching_path(path_import_aliases: set[str], path_check: str):
        """Recursively find the longest matching path in path_import_aliases."""
        # Base case
        if not path_check or path_check == "/":
            return None

        # Recursive case
        if path_check in path_import_aliases:
            return path_check
        elif f"{path_check}/" in path_import_aliases:
            return f"{path_check}/"
        else:
            return TSConfig._find_matching_path(path_import_aliases, os.path.dirname(path_check))

    @property
    def base_config(self) -> "TSConfig | None":
        """Returns the base TSConfig that this config inherits from.

        Gets the base configuration file that this TSConfig extends. The base configuration is used for inheriting settings like paths, baseUrl,and other compiler options.

        Returns:
            TSConfig | None: The parent TSConfig object if this config extends another config file, None otherwise.
        """
        return self._base_config

    @property
    def base_url(self) -> str | None:
        """Returns the base URL defined in the TypeScript configuration.

        This property retrieves the baseUrl from the project's TypeScript configuration file.
        The baseUrl is used for resolving non-relative module names.

        Returns:
            str | None: The base URL if defined in the config file or inherited from a base config,
                None if not specified.
        """
        return self._base_url

    @property
    def out_dir(self) -> str | None:
        """Returns the outDir defined in the TypeScript configuration.

        The outDir specifies the output directory for all emitted files. When specified, .js (as well as .d.ts, .js.map, etc.)
        files will be emitted into this directory. The directory structure of the source files is preserved.

        Returns:
            str | None: The output directory path if specified in the config file or inherited from a base config,
                None if not specified.
        """
        return self._out_dir

    @property
    def root_dir(self) -> str | None:
        """Returns the rootDir defined in the TypeScript configuration.

        The rootDir specifies the root directory of input files. This is used to control the output directory structure
        with outDir. When TypeScript compiles files, it maintains the directory structure of the source files relative
        to rootDir when generating output.

        Returns:
            str | None: The root directory path if specified in the config file or inherited from a base config,
                None if not specified.
        """
        return self._root_dir

    @property
    def root_dirs(self) -> list[str]:
        """Returns the rootDirs defined in the TypeScript configuration.

        The rootDirs allows a list of root directories to be specified that are merged and treated as one virtual directory.
        This can be used when your project structure doesn't match your runtime expectations. For example, when you have
        both generated and hand-written source files that need to appear to be in the same directory at runtime.

        Returns:
            list[str]: A list of root directory paths specified in the config file or inherited from a base config.
                Returns an empty list if not specified.
        """
        if self._root_dirs is not None:
            return self._root_dirs
        elif self.root_dir is not None:
            return [self.root_dir]
        return []

    @property
    def paths(self) -> dict[str, list[str]]:
        """Returns all custom module path mappings defined in the tsconfig file.

        Retrieves path mappings from both the current tsconfig file and any inherited base config file,
        translating all relative paths to absolute paths.

        Returns:
            dict[str, list[str]]: A dictionary mapping path patterns to lists of absolute path destinations.
                Each key is a path pattern (e.g., '@/*') and each value is a list of corresponding
                absolute path destinations.
        """
        return self._paths

    @property
    def references(self) -> list[Directory | File]:
        """Returns a list of directories that this TypeScript configuration file depends on.

        The references are defined in the 'references' field of the tsconfig.json file. These directories
        are used to resolve import conflicts and narrow the search space for import resolution.

        Returns:
            list[Directory | File | TSConfig]: A list of Directory, File, or TSConfig objects representing the dependent directories.
        """
        return self._references

    @property
    def path_import_aliases(self) -> dict[str, list[str]]:
        """Returns a formatted version of the paths property from a TypeScript configuration file.

        Processes the paths dictionary by formatting path patterns and their corresponding target paths. All wildcards (*), trailing slashes, and double
        slashes are removed from both the path patterns and their target paths. Target paths are also converted from relative to absolute paths.

        Returns:
            dict[str, list[str]]: A dictionary where keys are formatted path patterns and values are lists of formatted absolute target paths.
        """
        return self._path_import_aliases

    @property
    def reference_import_aliases(self) -> dict[str, list[str]]:
        """Returns a formatted version of the references property from a TypeScript configuration file.

        Processes the references dictionary by formatting reference paths and their corresponding target paths. For each
        reference, retrieves its tsconfig file and path mappings. Also includes any path mappings inherited from base
        configs.

        Returns:
            dict[str, list[str]]: A dictionary where keys are formatted reference paths (e.g. 'module/dist') and values
                are lists of absolute target paths derived from the referenced tsconfig's rootDirs and outDir settings.
        """
        return {k: [str(self.config_file.ctx.to_relative(v)) for v in vs] for k, vs in self._reference_import_aliases.items()}
