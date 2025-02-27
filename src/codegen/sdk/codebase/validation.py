from __future__ import annotations

import functools
import socket
from collections import Counter, defaultdict
from enum import StrEnum
from typing import TYPE_CHECKING

from tabulate import tabulate

from codegen.sdk.enums import NodeType
from codegen.sdk.utils import truncate_line
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from rustworkx import PyDiGraph

    from codegen.sdk.core.codebase import CodebaseType


class PostInitValidationStatus(StrEnum):
    NO_NODES = "NO_NODES"
    NO_EDGES = "NO_EDGES"
    MISSING_FILES = "MISSING_FILES"
    LOW_IMPORT_RESOLUTION_RATE = "LOW_IMPORT_RESOLUTION_RATE"
    SUCCESS = "SUCCESS"


def post_init_validation(codebase: CodebaseType) -> PostInitValidationStatus:
    """Post codebase._init_graph verifies that the built graph is valid."""
    from codegen.sdk.codebase.codebase_context import GLOBAL_FILE_IGNORE_LIST

    # Verify the graph has nodes
    if len(codebase.ctx.nodes) == 0:
        return PostInitValidationStatus.NO_NODES

    # Verify the graph has the same number of files as there are in the repo
    if len(codebase.files) != len(list(codebase.op.iter_files(codebase.ctx.projects[0].subdirectories, extensions=codebase.ctx.extensions, ignore_list=GLOBAL_FILE_IGNORE_LIST))):
        return PostInitValidationStatus.MISSING_FILES

    # Verify import resolution
    num_resolved_imports = len([imp for imp in codebase.imports if imp.imported_symbol and imp.imported_symbol.node_type != NodeType.EXTERNAL])
    if len(codebase.imports) > 0 and num_resolved_imports / len(codebase.imports) < 0.2:
        logger.info(f"Codebase {codebase.repo_path} has {num_resolved_imports / len(codebase.imports)} < 0.2 resolved imports")
        return PostInitValidationStatus.LOW_IMPORT_RESOLUTION_RATE
    return PostInitValidationStatus.SUCCESS


def post_reset_validation(init_nodes, nodes, init_edges, edges, repo_name: str, subdirectories: list[str] | None) -> None:
    logger.info("Verifying graph state and alerting if necessary")
    hostname = socket.gethostname()

    if len(dict.fromkeys(nodes)) != len(dict.fromkeys(init_nodes)):
        post_message = f"Reset graph: Nodes do not match for {repo_name} for subdirectories {subdirectories}. Hostname: {hostname}"
        message = get_nodes_error(init_nodes, nodes)
        log_or_throw(post_message, message)
    if len(dict.fromkeys(edges)) != len(dict.fromkeys(init_edges)):
        post_message = f"Reset graph: Edges do not match for {repo_name} for subdirectories {subdirectories}. Hostname: {hostname}"
        message = get_edges_error(edges, init_edges)
        log_or_throw(post_message, message)


def post_sync_validation(codebase: CodebaseType) -> bool:
    """Post codebase.sync, checks that the codebase graph is in a valid state (i.e. not corrupted by codebase.sync)"""
    if len(codebase.ctx.all_syncs) > 0 or len(codebase.ctx.pending_syncs) > 0 or len(codebase.ctx.transaction_manager.to_commit()) > 0:
        msg = "Can only be called on a reset codebase"
        raise NotImplementedError(msg)
    if not codebase.ctx.config.codebase.track_graph:
        msg = "Can only be called with track_graph=true"
        raise NotImplementedError(msg)
    return len(dict.fromkeys(codebase.ctx.old_graph.nodes())) == len(dict.fromkeys(codebase.ctx.nodes)) and len(dict.fromkeys(codebase.ctx.old_graph.weighted_edge_list())) == len(
        dict.fromkeys(codebase.ctx.edges)
    )


def log_or_throw(message, thread_message: str):
    hostname = socket.gethostname()
    logger.error(message)
    # logger.error(thread_message)
    if hostname != "modal":
        msg = f"{message}\n{thread_message}"
        raise Exception(msg)
    return


def get_edges_error(edges, init_edges):
    set_edges = set(edges)
    set_init_edges = set(init_edges)
    missing_edges = set_init_edges - set_edges
    extra_edges = set_edges - set_init_edges
    message = ""
    if extra_edges:
        extras = tabulate((map(functools.partial(truncate_line, max_chars=50), edge) for edge in extra_edges), ["Start", "End", "Edge"], maxcolwidths=50)
        message += f"""
Extra edges
```
{extras}
```
"""

    if missing_edges:
        missing = tabulate((map(functools.partial(truncate_line, max_chars=50), edge) for edge in missing_edges), ["Start", "End", "Edge"], maxcolwidths=50)
        message += f"""
Missing edges
```
{missing}
```
"""
    missing_by_key = defaultdict(lambda: defaultdict(list))
    for u, v, data in missing_edges:
        missing_by_key[u][v].append(data)
    for u, v, data in extra_edges:
        if u in missing_by_key and v in missing_by_key[u]:
            for match in missing_by_key[u][v]:
                message += f"Possible match from {u} to {v}: {match} -> {data}\n"
    if len(edges) != len(set_init_edges):
        message += f"{len(edges) - len(set_edges)} edges duplicated from {len(init_edges) - len(set_init_edges)}. Printing out up to 5 edges\n"
        extras = tabulate(((*map(functools.partial(truncate_line, max_chars=50), edge), count) for edge, count in Counter(edges).most_common(5)), ["Start", "End", "Edge", "Count"], maxcolwidths=50)
        message += extras
    return message


def get_nodes_error(init_nodes, nodes):
    set_nodes = set(nodes)
    set_init_nodes = set(init_nodes)
    message = f"""
Extra nodes
```
{set_nodes - set_init_nodes}
```

Missing nodes
```
{set_init_nodes - set_nodes}
```
"""
    for node in set_nodes - set_init_nodes:
        from codegen.sdk.core.external_module import ExternalModule

        if isinstance(node, ExternalModule):
            message += "External Module persisted with following dependencies: " + str(list((node.ctx.get_node(source), edge) for source, _, edge in node.ctx.in_edges(node.node_id)))
    return message


def get_edges(graph: PyDiGraph):
    ret = []
    for start, end, edge in graph.weighted_edge_list():
        ret.append((graph.get_node_data(start), graph.get_node_data(end), edge))
    return ret
