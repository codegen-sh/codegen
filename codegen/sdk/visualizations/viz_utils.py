import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING

import networkx as nx
from networkx import DiGraph, Graph

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.output.utils import DeterministicJSONEncoder
from codegen.sdk.visualizations.enums import GraphJson, GraphType

if TYPE_CHECKING:
    from codegen.sdk.git.repo_operator.repo_operator import RepoOperator

####################################################################################################################
# READING GRAPH VISUALIZATION DATA
####################################################################################################################


def get_graph_json(op: "RepoOperator"):
    if os.path.exists(op.viz_file_path):
        with open(op.viz_file_path) as f:
            graph_json = json.load(f)
        return graph_json
    else:
        return None


####################################################################################################################
# NETWORKX GRAPH TO JSON
####################################################################################################################


def get_node_options(node: Editable | str | int):
    if isinstance(node, Editable):
        return asdict(node.viz)
    return {}


def get_node_id(node: Editable | str | int):
    if isinstance(node, Importable):
        return node.node_id
    elif isinstance(node, Editable):
        return str(node.span)
    elif isinstance(node, str) or isinstance(node, int):
        return node


def graph_to_json(G1: Graph, root: Editable | str | int | None = None):
    G2 = DiGraph()
    for node_tuple in G1.nodes(data=True):
        options = get_node_options(node_tuple[0])
        options.update(node_tuple[1])
        G2.add_node(get_node_id(node_tuple[0]), **options)

    for edge_tuple in G1.edges(data=True):
        options = edge_tuple[2]
        if "symbol" in options:
            print(get_node_options(options["symbol"]))
            options.update(get_node_options(options["symbol"]))
            del options["symbol"]
        G2.add_edge(get_node_id(edge_tuple[0]), get_node_id(edge_tuple[1]), **options)

    if root:
        root = get_node_id(root)
        return json.dumps(asdict(GraphJson(type=GraphType.TREE.value, data=nx.tree_data(G2, root))), cls=DeterministicJSONEncoder, indent=2)
    else:
        return json.dumps(asdict(GraphJson(type=GraphType.GRAPH.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)
