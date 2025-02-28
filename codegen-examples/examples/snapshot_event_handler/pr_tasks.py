import logging
from codegen.agents.code_agent import CodeAgent
from codegen.extensions.github.types.pull_request import PullRequestLabeledEvent

from codegen.extensions.langchain.tools import GithubCreatePRCommentTool, GithubCreatePRReviewCommentTool, GithubViewPRTool
from codegen.sdk.core.codebase import Codebase

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def lint_for_dev_import_violations(codebase: Codebase, event: PullRequestLabeledEvent):
    # Next.js codemod to detect imports of the react-dev-overlay module in production code
    
    patch, commit_shas, modified_symbols = codebase.get_modified_symbols_in_pr(event.pull_request.number)
    modified_files = set(commit_shas.keys())
    from codegen.sdk.core.statements.if_block_statement import IfBlockStatement

    DIR_NAME = 'packages/next/src/client/components/react-dev-overlay'
    directory = codebase.get_directory(DIR_NAME)

    violations = []


    false_operators = ["!=", "!=="]
    true_operators = ["===", "=="]



    def is_valid_block_expression(if_block: IfBlockStatement) -> bool:
        """Check if the if block has a valid environment check condition.
        
        Valid conditions are:
        - process.env.NODE_ENV !== 'production'
        - process.env.NODE_ENV != 'production'
        - process.env.NODE_ENV === 'development'
        - process.env.NODE_ENV == 'development'
        """
        if not if_block.is_if_statement:
            return False
            
        condition = if_block.condition
        # Get the operator without any whitespace
        operator = condition.operator[-1].source
        
        # Check for non-production conditions
        if operator in false_operators and condition.source == f"process.env.NODE_ENV {operator} 'production'":
            return True
            
        # Check for explicit development conditions
        if operator in true_operators and condition.source == f"process.env.NODE_ENV {operator} 'development'":
            return True
            
        return False


    def process_else_block_expression(else_block: IfBlockStatement) -> bool:
        """Check if the else block is valid by checking its parent if block.
        
        Valid when the parent if block checks for production environment:
        - if (process.env.NODE_ENV === 'production') { ... } else { <our import> }
        - if (process.env.NODE_ENV == 'production') { ... } else { <our import> }
        """
        if not else_block.is_else_statement:
            return False
            
        main_if = else_block._main_if_block
        if not main_if or not main_if.condition:
            return False
            
        condition = main_if.condition
        operator = condition.operator[-1].source
        
        # Valid if the main if block checks for production
        return operator in true_operators and condition.source == f"process.env.NODE_ENV {operator} 'production'"


    for file in directory.files(recursive=True):
        for imp in file.inbound_imports:

            if imp.file.filepath not in modified_files:
                # skip if the import is not in the pull request's modified files
                continue
            # Skip if the import is from within the target directory
            if directory.dirpath in imp.file.filepath:
                # "✅ Valid import" if the import is within the target directory
                continue
                
            parent_if_block = imp.parent_of_type(IfBlockStatement)
            
            # Check if import is in a valid environment check block
            if_block_valid = parent_if_block and is_valid_block_expression(parent_if_block)
            else_block_valid = parent_if_block and process_else_block_expression(parent_if_block)
            
            # Skip if the import is properly guarded by environment checks
            if if_block_valid or else_block_valid:
                # "✅ Valid import" these are guarded by non prod checks
                continue

            # Report invalid imports that aren't properly guarded
            violation = f"- Violation in `{file.filepath}`: Importing from `{imp.file.filepath}` ([link]({imp.github_url}))"
            violations.append(violation)
            logger.info(f"Found violation: {violation}")


    if violations:
        # Comment on PR with violations
        review_attention_message = "## Dev Import Violations Found\n\n"
        review_attention_message += "The following files have imports that violate development overlay rules:\n\n"
        review_attention_message += "\n".join(violations)
        review_attention_message += "\n\nPlease ensure that development imports are not imported in production code."

        # Create PR comment with the formatted message
        codebase._op.create_pr_comment(event.pull_request.number, review_attention_message)