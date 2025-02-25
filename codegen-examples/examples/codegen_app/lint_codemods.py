import logging
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.sdk.core.codebase import Codebase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def pr_lint_dev_import_violations(codebase: Codebase, event: PullRequestLabeledEvent):
    
    patch, commit_shas, modified_symbols = codebase.get_modified_symbols_in_pr(event.pull_request.number)
    modified_files = set(commit_shas.keys())

    DIR_NAME = 'packages/next/src/client/components/react-dev-overlay'
    directory = codebase.get_directory(DIR_NAME)

    # Initialize a list to store all violations
    violations = []
    
    # Check if directory exists before proceeding
    if directory is not None and hasattr(directory, 'files'):
        for file in directory.files:
            for imp in file.inbound_imports:
                # Check if the import is from outside the directory and is in the modified files
                if imp.file not in directory and imp.file.filepath in modified_files:
                    # Skip require statements
                    if 'require' in imp.import_statement:
                        continue
                    violation = f'- Violation in `{file.filepath}`: Importing from `{imp.file.filepath}` ([link]({imp.github_url}))'
                    violations.append(violation)
                    logger.info(f"Found violation: {violation}")
        
        # Only create a PR comment if violations are found
        if violations:
            review_attention_message = "## Dev Import Violations Found\n\n"
            review_attention_message += "The following files have imports that violate development overlay rules:\n\n"
            review_attention_message += "\n".join(violations)
            review_attention_message += "\n\nPlease ensure that development imports are not imported in production code."
            
            # Create PR comment with the formatted message
            codebase._op.create_pr_comment(event.pull_request.number, review_attention_message)

    