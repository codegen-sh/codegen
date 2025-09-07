Design graph-sitter config enrichment integration
Additional parameters:
https://github.com/Zeeeepa/codegen/blob/develop/src/codegen/sdk/configs/models/codebase.py (To extend this). wtih:


lsp_diagnostics=true   (from extensions/lsp/solidlsp) + (codegen/src/codegen/sdk/extensions/tools) + (codegen/src/codegen/sdk/extensions/autogenlib)
error_auto_resolve=true   (from full context - to more effectively resolve errors, type mismatches and other errors/ issues - CORE TOOLS ARE IN (codegen/src/codegen/sdk/extensions/tools))
doc_gen=true   (codegen/src/codegen/sdk/extensions/tools) - to create .md documentation of all files and their parameters/ usages / etc. 



lsp_diagnostics = 


Package Deployment Structure
5 Separate Packages:
pip install -e. should install = 

codegen - Main package with agent functionality  (codegen/src/codegen)
graph-sitter-sdk - Core SDK with 5-parameter system  (codegen/src/codegen/sdk)
autogenlib - Context enhancement and code generation (codegen/src/codegen/sdk/extensions/autogenlib)
solidlsp - LSP server management and protocol handling (codegen/src/codegen/sdk/extensions/lsp/solidlsp)
codegen-api-client - API client for remote operations  (codegen/src/codegen/codegen_api_client)



YOUR PLAN : 
Document all analyzed components with capabilities and integration points
First view 
codegen/src/codegen/sdk/extensions/tools:

bash.py
codebase_analysis.py
codegen_sdk_codebase.py
current_code_codebase.py
document_functions.py
generate_docs_json.py
list_directory.py
mdx_docs_generation.py
observation.py
reflection.py
reveal_symbol.py
reveal_symbol_fn.py
tool_output_types.py
tools.py
view_file.py

Second View:
codegen/src/codegen/sdk/extensions/autogenlib

__init__.py
_cache.py
_caller.py
_context.py
_exception_handler.py
_finder.py
_generator.py
_state.py

Third View:
codegen/src/codegen/sdk/extensions/lsp/solidlsp
language_servers
lsp_protocol_handler
util
.gitignore
__init__.py
ls.py
ls_config.py
ls_exceptions.py
ls_handler.py
ls_logger.py
ls_request.py
ls_types.py
ls_utils.py
settings.py


Design separate deployable package structure for all components
Create framework to integrate all tools/ directory capabilities
Create integration layer for SolidLSP language servers and diagnostics
Integrate AutogenLib for enhanced context analysis capabilities
Design multi-source context aggregation pipeline for error analysis / context / resolution / document creation / 
