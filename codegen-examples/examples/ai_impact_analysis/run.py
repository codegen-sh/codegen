import sys
import traceback
import os

from codegen import Codebase
from codegen.extensions.attribution.cli import run
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.config import ProjectConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage

if __name__ == "__main__":
    try:
        print("Initializing codebase...")

        # Option A: Use current directory if it's a git repository
        if os.path.exists(".git"):
            print("Using current directory as repository...")
            # Create a repo operator for the current directory
            repo_path = os.getcwd()
            repo_config = RepoConfig.from_repo_path(repo_path)
            repo_operator = RepoOperator(repo_config=repo_config)

            # Initialize codebase with a project config
            project = ProjectConfig.from_repo_operator(repo_operator=repo_operator, programming_language=ProgrammingLanguage.PYTHON)
            codebase = Codebase(projects=[project])
        else:
            # Option B: Try to find a git repository in parent directories
            print("Searching for git repository in parent directories...")
            current_dir = os.getcwd()
            found_git = False

            while current_dir != os.path.dirname(current_dir):  # Stop at root
                if os.path.exists(os.path.join(current_dir, ".git")):
                    print(f"Found git repository at {current_dir}")
                    repo_config = RepoConfig.from_repo_path(current_dir)
                    repo_operator = RepoOperator(repo_config=repo_config)

                    # Initialize codebase with a project config
                    project = ProjectConfig.from_repo_operator(repo_operator=repo_operator, programming_language=ProgrammingLanguage.PYTHON)
                    codebase = Codebase(projects=[project])
                    found_git = True
                    break
                current_dir = os.path.dirname(current_dir)

            if not found_git:
                # Option C: Use from_repo method which handles cloning
                print("No local git repository found. Cloning a repository...")
                codebase = Codebase.from_repo(repo_full_name="codegen-sh/codegen", language="python")

        print(f"Codebase loaded with {len(codebase.files)} files and {len(codebase.symbols)} symbols")

        # Run the analysis
        run(codebase)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        sys.exit(1)
