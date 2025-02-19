import codegen
import networkx as nx
from codegen import Codebase


@codegen.function("visualize-modules-dependencies")
def run(codebase: Codebase):
    # Create a directed graph
    G = nx.DiGraph()

    list_apps = ["src/sentry/api", "src/sentry/auth", "src/sentry/flags"]
    # Get the specific file for balance
    for app in list_apps:
        G.add_node(app, metadata={"color": "red"})

    for app in list_apps:
        for file in codebase.files:
            if app in file.filepath:
                # Iterate over all import statements in the file
                for import_statement in file.import_statements:
                    # Check if the import statement is importing an app
                    for imp in import_statement.imports:
                        # Assuming app imports follow a specific naming convention or structure
                        if "app" in imp.name:  # Adjust this condition based on your app naming convention
                            G.add_edge(app, imp.import_statement.source)

    nodes_to_remove = [node for node, degree in G.degree() if degree == 1]

    # Remove the nodes from the graph
    G.remove_nodes_from(nodes_to_remove)

    print(G)
    print("Use codegen.sh to visualize the graph!")


if __name__ == "__main__":
    codebase = Codebase.from_repo("getsentry/sentry", commit="fb0d53b2210cc896fc3e2cf32dae149ea8a8a45a", language="python")
    run(codebase)
