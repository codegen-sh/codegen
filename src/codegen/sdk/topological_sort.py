import rustworkx as nx
from rustworkx import DAGHasCycle, PyDiGraph

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def pseudo_topological_sort(graph: PyDiGraph, flatten: bool = True):
    """This will come up with an ordering of nodes within the graph respecting topological"""
    try:
        # Try to perform a topological sort
        sorted_nodes = list(nx.topological_sort(graph))
        return sorted_nodes
    except DAGHasCycle:
        # If a cycle is detected, handle it separately
        logger.warning("The graph contains a cycle. Performing an approximate topological sort.")

        # Find the strongly connected components in the graph
        sccs = list(nx.strongly_connected_components(graph))

        if not flatten:
            return sccs

        # Create a new graph with each strongly connected component as a single node
        scc_graph = nx.PyDiGraph()
        for i, scc in enumerate(sccs):
            scc_graph.add_node(i)

        for u, v in graph.edges():
            scc_u = next((i for i, scc in enumerate(sccs) if u in scc), None)
            scc_v = next((i for i, scc in enumerate(sccs) if v in scc), None)
            if scc_u is None or scc_v is None:
                continue
            if scc_u != scc_v:
                scc_graph.add_edge(scc_u, scc_v, None)

        # Perform a topological sort on the condensed graph
        sorted_sccs = list(nx.topological_sort(scc_graph))

        # Expand the strongly connected components back to individual nodes
        sorted_nodes = [node for scc_idx in sorted_sccs for node in sccs[scc_idx]]

        return sorted_nodes
