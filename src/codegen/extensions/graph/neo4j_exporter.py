from neo4j import GraphDatabase

from codegen.extensions.graph.utils import SimpleGraph


class Neo4jExporter:
    """Class to handle exporting the codebase graph to Neo4j."""

    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships in the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def export_graph(self, graph: SimpleGraph):
        """Export the SimpleGraph to Neo4j."""
        self.clear_database()

        with self.driver.session() as session:
            # Create nodes
            for node in graph.nodes.values():
                properties = {"name": node.name, "full_name": node.full_name, **{k: str(v) if isinstance(v, (dict, list)) else v for k, v in node.properties.items()}}

                query = f"CREATE (n:{node.label} {{{', '.join(f'{k}: ${k}' for k in properties.keys())}}})"
                session.run(query, properties)

            # Create relationships
            for relation in graph.relations:
                source_node = graph.nodes[relation.source_id]
                target_node = graph.nodes[relation.target_id]

                properties = {**{k: str(v) if isinstance(v, (dict, list)) else v for k, v in relation.properties.items()}}

                query = (
                    f"MATCH (source:{source_node.label} {{full_name: $source_name}}), "
                    f"(target:{target_node.label} {{full_name: $target_name}}) "
                    f"CREATE (source)-[r:{relation.label} "
                    f"{{{', '.join(f'{k}: ${k}' for k in properties.keys())}}}]->"
                    f"(target)"
                )

                session.run(query, {"source_name": source_node.full_name, "target_name": target_node.full_name, **properties})
