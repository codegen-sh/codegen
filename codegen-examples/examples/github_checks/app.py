import logging

import modal
from codegen import CodegenApp, Codebase
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment
from dotenv import load_dotenv
import networkx as nx

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cg = CodegenApp(name="codegen-github-checks")


def create_graph_from_codebase(repo_path):
    """Create a directed graph representing import relationships in a codebase."""
    codebase = Codebase.from_repo(repo_path)
    G = nx.MultiDiGraph()

    for imp in codebase.imports:
        if imp.from_file and imp.to_file:
            G.add_edge(
                imp.to_file.filepath,
                imp.from_file.filepath,
                color="red" if getattr(imp, "is_dynamic", False) else "black",
                label="dynamic" if getattr(imp, "is_dynamic", False) else "static",
                is_dynamic=getattr(imp, "is_dynamic", False),
            )
    return G


def convert_all_calls_to_kwargs(codebase):
    for file in codebase.files:
        for function_call in file.function_calls:
            function_call.convert_args_to_kwargs()

    print("All function calls have been converted to kwargs")


def find_import_cycles(G):
    """Identify strongly connected components (cycles) in the import graph."""
    cycles = [scc for scc in nx.strongly_connected_components(G) if len(scc) > 1]
    print(f"🔄 Found {len(cycles)} import cycles.")

    for i, cycle in enumerate(cycles, 1):
        print(f"\nCycle #{i}: Size {len(cycle)} files")
        print(f"Total number of imports in cycle: {G.subgraph(cycle).number_of_edges()}")

        print("\nFiles in this cycle:")
        for file in cycle:
            print(f"  - {file}")

    return cycles


def find_problematic_import_loops(G, cycles):
    """Identify cycles with both static and dynamic imports between files."""
    problematic_cycles = []

    for i, scc in enumerate(cycles):
        if i == 2:
            continue

        mixed_imports = {}
        for from_file in scc:
            for to_file in scc:
                if G.has_edge(from_file, to_file):
                    edges = G.get_edge_data(from_file, to_file)
                    dynamic_count = sum(1 for e in edges.values() if e["color"] == "red")
                    static_count = sum(1 for e in edges.values() if e["color"] == "black")

                    if dynamic_count > 0 and static_count > 0:
                        mixed_imports[(from_file, to_file)] = {
                            "dynamic": dynamic_count,
                            "static": static_count,
                            "edges": edges,
                        }

        if mixed_imports:
            problematic_cycles.append({"files": scc, "mixed_imports": mixed_imports, "index": i})

    print(f"Found {len(problematic_cycles)} cycles with potentially problematic imports.")

    for i, cycle in enumerate(problematic_cycles):
        print(f"\n⚠️ Problematic Cycle #{i + 1} (Index {cycle['index']}): Size {len(cycle['files'])} files")
        print("\nFiles in cycle:")
        for file in cycle["files"]:
            print(f"  - {file}")
        print("\nMixed imports:")
        for (from_file, to_file), imports in cycle["mixed_imports"].items():
            print(f"\n  From: {from_file}")
            print(f"  To:   {to_file}")
            print(f"  Static imports: {imports['static']}")
            print(f"  Dynamic imports: {imports['dynamic']}")

    return problematic_cycles


@cg.github.event("pull_request:labeled")
def handle_pr(event: PullRequestLabeledEvent):
    codebase = Codebase.from_repo(event.repository.get("full_name"), commit=event.pull_request.head.sha)

    G = create_graph_from_codebase(event.repository.get("full_name"))
    cycles = find_import_cycles(G)
    problematic_loops = find_problematic_import_loops(G, cycles)

    # Build comment message
    message = ["### Import Cycle Analysis - GitHub Check\n"]

    if problematic_loops:
        message.append("\n### ⚠️ Potentially Problematic Import Cycles")
        message.append("Cycles with mixed static and dynamic imports, which might recquire attention.")
        for i, cycle in enumerate(problematic_loops, 1):
            message.append(f"\n#### Problematic Cycle {i}")
            for (from_file, to_file), imports in cycle["mixed_imports"].items():
                message.append(f"\nFrom: `{from_file}`")
                message.append(f"To: `{to_file}`")
                message.append(f"- Static imports: {imports['static']}")
                message.append(f"- Dynamic imports: {imports['dynamic']}")
    else:
        message.append("\nNo problematic import cycles found! 🎉")

    create_pr_comment(
        codebase,
        event.pull_request.number,
        "\n".join(message),
    )

    return {
        "message": "PR event handled",
        "num_files": len(codebase.files),
        "num_functions": len(codebase.functions),
    }


base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        "codegen",
    )
)

app = modal.App("codegen-import-cycles-github-check")


@app.function(image=base_image, secrets=[modal.Secret.from_dotenv()])
@modal.asgi_app()
def fastapi_app():
    print("Starting codegen fastapi app")
    return cg.app
