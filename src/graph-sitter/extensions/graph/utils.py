import uuid
from dataclasses import dataclass, field
from enum import Enum


class NodeLabel(Enum):
    CLASS = "Class"
    METHOD = "Method"
    FUNCTION = "Func"


class RelationLabel(Enum):
    DEFINES = "DEFINES"
    INHERITS_FROM = "INHERITS_FROM"
    CALLS = "CALLS"


@dataclass(kw_only=True)
class BaseNode:
    label: str
    properties: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __hash__(self):
        """Make the relation hashable based on its id."""
        return hash(self.id)

    def __eq__(self, other):
        """Define equality based on id."""
        if not isinstance(other, Relation):
            return NotImplemented
        return self.id == other.id


@dataclass(kw_only=True)
class Node(BaseNode):
    """Simple node class with label and properties."""

    name: str
    full_name: str


@dataclass(kw_only=True)
class Relation(BaseNode):
    """Simple relation class connecting two nodes."""

    source_id: str
    target_id: str

    def __hash__(self):
        """Make the relation hashable based on its id."""
        return hash(self.id)

    def __eq__(self, other):
        """Define equality based on id."""
        if not isinstance(other, Relation):
            return NotImplemented
        return self.id == other.id


class SimpleGraph:
    """Basic graph implementation using sets of nodes and relations."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.relations: set[Relation] = set()
        self.existing_relations: set[str] = set()

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_relation(self, relation: Relation) -> None:
        """Add a relation to the graph."""
        related_nodes = f"{relation.source_id}->{relation.label}->{relation.target_id}"
        if relation.source_id in self.nodes and relation.target_id in self.nodes and related_nodes not in self.existing_relations:
            self.relations.add(relation)
            self.existing_relations.add(related_nodes)
