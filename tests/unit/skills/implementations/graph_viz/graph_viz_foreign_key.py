from abc import ABC

import networkx as nx

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

PyForeignKeyGraphTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from app.models.base import BaseModel

class UserModel(BaseModel):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

class TaskModel(BaseModel):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

class CommentModel(BaseModel):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    content = Column(String(500), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

class ProjectModel(BaseModel):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))

class TaskProjectModel(BaseModel):
    __tablename__ = 'task_projects'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

class AgentRunModel(BaseModel):
    __tablename__ = 'agent_runs'

    id = Column(BigInteger, primary_key=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(BigInteger, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)

class AgentModel(BaseModel):
    __tablename__ = 'agents'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
""",
            filepath="app/models/schema.py",
        )
    ],
    graph=True,
)


@skill(
    eval_skill=False,
    prompt="Help me analyze my data schema. I have a bunch of SQLAlchemy models with foreign keys to each other, all of them are classes like this that inherit BaseModel, like the one in this file.",
    uid="2a5d8f4d-5f02-445e-9d00-77bdb9a0d268",
)
class ForeignKeyGraph(Skill, ABC):
    """This skill helps analyze a data schema by creating a graph representation of SQLAlchemy models and their foreign key relationships.

    It processes a collection of SQLAlchemy models with foreign keys referencing each other. All of these models are classes that inherit from BaseModel, similar to the one in this file. Foreign keys
    are typically defined in the following format:
    agent_run_id = Column(BigInteger, ForeignKey("AgentRun.id", ondelete="CASCADE"), nullable=False)

    The skill iterates through all classes in the codebase, identifying those that are subclasses of BaseModel. For each relevant class, it examines the attributes to find ForeignKey definitions. It
    then builds a mapping of these relationships.

    Using this mapping, the skill constructs a directed graph where:
    - Nodes represent the models (with the 'Model' suffix stripped from their names)
    - Edges represent the foreign key relationships between models

    This graph visualization allows for easy analysis of the data schema, showing how different models are interconnected through their foreign key relationships. The resulting graph can be used to
    understand data dependencies, optimize queries, or refactor the database schema.
    """

    @staticmethod
    @skill_impl(test_cases=[PyForeignKeyGraphTest], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Create a mapping dictionary to hold relationships
        foreign_key_mapping = {}

        # Iterate through all classes in the codebase
        for cls in codebase.classes:
            # Check if the class is a subclass of BaseModel and defined in the correct file
            if cls.is_subclass_of("BaseModel") and "from app.models.base import BaseModel" in cls.file.content:
                # Initialize an empty list for the current class
                foreign_key_mapping[cls.name] = []

                # Iterate through the attributes of the class
                for attr in cls.attributes:
                    # Check if the attribute's source contains a ForeignKey definition
                    if "ForeignKey" in attr.source:
                        # Extract the table name from the ForeignKey string
                        start_index = attr.source.find('("') + 2
                        end_index = attr.source.find(".id", start_index)
                        if end_index != -1:
                            target_table = attr.source[start_index:end_index]
                            # Append the target table to the mapping, avoiding duplicates
                            if target_table not in foreign_key_mapping[cls.name]:
                                foreign_key_mapping[cls.name].append(target_table)

        # Now foreign_key_mapping contains the desired relationships
        # print(foreign_key_mapping)

        # Create a directed graph
        G = nx.DiGraph()

        # Iterate through the foreign_key_mapping to add nodes and edges
        for model, targets in foreign_key_mapping.items():
            # Add the model node (strip 'Model' suffix)
            model_name = model.replace("Model", "")
            G.add_node(model_name)

            # Add edges to the target tables
            for target in targets:
                G.add_node(target)  # Ensure the target is also a node
                G.add_edge(model_name, target)

        # Now G contains the directed graph of models and their foreign key relationships
        # You can visualize or analyze the graph as needed
        codebase.visualize(G)

        ##############################################################################################################
        # IN DEGREE
        ##############################################################################################################

        # Calculate in-degrees for each node
        in_degrees = G.in_degree()

        # Create a list of nodes with their in-degree counts
        in_degree_list = [(node, degree) for node, degree in in_degrees]

        # Sort the list by in-degree in descending order
        sorted_in_degrees = sorted(in_degree_list, key=lambda x: x[1], reverse=True)

        # Print the nodes with their in-degrees
        for node, degree in sorted_in_degrees:
            print(f"Node: {node}, In-Degree: {degree}")
            if degree == 0:
                G.nodes[node]["color"] = "red"

        ##############################################################################################################
        # FIND MODELS MAPPING TO TASK
        ##############################################################################################################

        # Collect models that map to the Task model
        models_mapping_to_task = []
        for model, targets in foreign_key_mapping.items():
            if "Task" in targets:
                models_mapping_to_task.append(model)

        # Print the models that map to Task
        print("Models mapping to 'Task':")
        for model in models_mapping_to_task:
            print(f"> {model}")
