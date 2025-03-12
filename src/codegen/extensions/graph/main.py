from codegen.extensions.graph.create_graph import create_codebase_graph
from codegen.extensions.graph.neo4j_exporter import Neo4jExporter
from codegen.sdk.core.codebase import Codebase


def visualize_codebase(codebase, neo4j_uri: str, username: str, password: str):
    """Create and visualize a codebase graph in Neo4j.

    Args:
        codebase: The codebase object to analyze
        neo4j_uri: URI for Neo4j database
        username: Neo4j username
        password: Neo4j password
    """
    # Create the graph using your existing function
    graph = create_codebase_graph(codebase)

    # Export to Neo4j
    exporter = Neo4jExporter(neo4j_uri, username, password)
    try:
        exporter.export_graph(graph)
        print("Successfully exported graph to Neo4j")

        # Print some useful Cypher queries for visualization
        print("\nUseful Cypher queries for visualization:")
        print("\n1. View all nodes and relationships:")
        print("MATCH (n)-[r]->(m) RETURN n, r, m")

        print("\n2. View class hierarchy:")
        print("MATCH (c:Class)-[r:INHERITS_FROM]->(parent:Class) RETURN c, r, parent")

        print("\n3. View methods defined by each class:")
        print("MATCH (c:Class)-[r:DEFINES]->(m:Method) RETURN c, r, m")

    finally:
        exporter.close()


if __name__ == "__main__":
    # Initialize codebase
    codebase = Codebase("../../", language="python")
    visualize_codebase(codebase, "bolt://localhost:7687", "neo4j", "password")
