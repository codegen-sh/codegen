def visualize_graph(graph):
    """
    Visualize SCC using Graphviz with a strictly enforced circular layout
    """
    import pygraphviz as pgv

    # Create a new pygraphviz graph directly (instead of converting)
    A = pgv.AGraph(strict=False, directed=True)

    # Set graph attributes for strict circular layout
    A.graph_attr.update(
        {
            "layout": "circo",
            "root": "circle",
            "splines": "curved",
            "overlap": "false",
            "sep": "+25,25",
            "pad": "0.5",
            "ranksep": "2.0",
            "nodesep": "0.8",
            "mindist": "2.0",
            "start": "regular",
            "ordering": "out",
            "concentrate": "false",
            "ratio": "1.0",
        }
    )

    # Set node attributes for consistent sizing
    A.node_attr.update({"shape": "circle", "fixedsize": "true", "width": "1.5", "height": "1.5", "style": "filled", "fillcolor": "lightblue", "fontsize": "11", "fontname": "Arial"})

    # Set default edge attributes
    A.edge_attr.update({"penwidth": "1.5", "arrowsize": "0.8", "len": "2.0", "weight": "1", "dir": "forward"})

    # Add nodes first
    for node in graph.nodes():
        short_name = node.split("/")[-1]
        A.add_node(node, label=short_name)

    # Add edges with their attributes
    for u, v, key, data in graph.edges(data=True, keys=True):
        # Create a unique key for this edge
        edge_key = f"{u}_{v}_{key}"

        # Set edge attributes based on the data
        edge_attrs = {
            "key": edge_key,  # Ensure unique edge
            "color": "red" if data.get("color") == "red" else "#666666",
            "style": "dashed" if data.get("color") == "red" else "solid",
            "label": "dynamic" if data.get("color") == "red" else "",
            "fontcolor": "red" if data.get("color") == "red" else "#666666",
            "fontsize": "10",
        }

        A.add_edge(u, v, **edge_attrs)

    # Force circo layout with specific settings
    A.layout(prog="circo")

    # Save with a larger size
    A.draw("import_cycle.png", format="png", prog="circo", args="-Gsize=12,12!")

    from IPython.display import Image

    return Image("import_cycle.png")
