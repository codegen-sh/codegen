import base64
import logging
import pickle
from pathlib import Path

import networkx as nx
from tabulate import tabulate

from codegen.sdk.codebase.factory.get_dev_customer_codebase import get_codebase_codegen
from codegen.shared.enums.programming_language import ProgrammingLanguage

logging.basicConfig(level=logging.INFO)
codegen = get_codebase_codegen("../codegen", ".")
res = []

# Create a directed graph
G = nx.DiGraph()

# Iterate through all files in the codebase
for file in codegen.files:
    if "test" not in file.filepath:
        if file.ctx.repo_name == "codegen":
            color = "yellow"
        elif file.ctx.repo_name == "codegen-sdk":
            color = "red"
            if file.ctx.base_path == "codegen-git":
                color = "green"
            elif file.ctx.base_path == "codegen-utils":
                color = "purple"
        else:
            color = "yellow"
        if file.ctx.programming_language == ProgrammingLanguage.TYPESCRIPT:
            color = "blue"

        # Add the file as a node
        G.add_node(file.filepath, color=color)

        # Iterate through all imports in the file
        for imp in file.imports:
            if imp.from_file:
                # print("way")
                # Add an edge from the current file to the imported file
                G.add_edge(file.filepath, imp.from_file.filepath)

for url, func in codegen.global_context.multigraph.api_definitions.items():
    usages = codegen.global_context.multigraph.usages.get(url, None)
    if usages:
        res.append((url, func.name, func.filepath, [usage.filepath + "::" + usage.name for usage in usages]))
        for usage in usages:
            G.add_edge(usage.filepath, func.filepath)
print(tabulate(res, headers=["URL", "Function Name", "Filepath", "Usages"]))
# Visualize the graph
# codebase.visualize(G)

# Print some basic statistics
print(f"Number of files: {G.number_of_nodes()}")
print(f"Number of import relationships: {G.number_of_edges()}")

# Serialize the graph to a pickle
graph_pickle = pickle.dumps(G)

# Convert to base64
graph_base64 = base64.b64encode(graph_pickle).decode("utf-8")

print(f"Base64 encoded graph size: {len(graph_base64)} bytes 🌈")
print(f"Base64 string: {graph_base64}")
Path("out.txt").write_text(graph_base64)
print()
