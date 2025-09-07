Design graph-sitter config enrichment integration
Additional parameters:
https://github.com/Zeeeepa/codegen/blob/develop/src/codegen/sdk/configs/models/codebase.py (To extend this). wtih:


diagnostics=true   (from extensions/lsp/solidlsp) + (codegen/src/codegen/sdk/extensions/tools) + (codegen/src/codegen/sdk/extensions/autogenlib)
error_auto_resolve=true   (from full context - to more effectively resolve errors, type mismatches and other errors/ issues - CORE TOOLS ARE IN (codegen/src/codegen/sdk/extensions/tools))
doc_gen=true   (codegen/src/codegen/sdk/extensions/tools) - to create .md documentation of all files and their parameters/ usages / etc. 

diagnostics=true → Unified diagnostic aggregation across all components  from lsp_diagnostics.py (to create in codegen/src/codegen/sdk/extensions/lsp/solidlsp) + from codegen/src/codegen/sdk/extensions/tools/codebase_analysis.py + 
error_auto_resolve=true → AI-powered resolution using SolidLSP + autogenlib + graph-sitter
doc_gen=true → Comprehensive documentation generation integration

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
README.md 


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
codegen/src/codegen/sdk/extensions/lsp/lsp_diagnostics.py (all diagnostics from lsp server about codebase files)
codegen/src/codegen/sdk/extensions/autogenlib/auto_resolve.py (provide error contexts to api to create error resolutions and apply them)- requires API KEY
codegen/src/codegen/sdk/extensions/autogenlib/enhance_context.py (enhance error contexts)
codegen/src/codegen/sdk/configs/models/codebase_enhanced.py (to include lsp_diagnostics=true, error_auto_resolve=true , doc_gen=true (created md documentation).
Create framework to integrate all tools/ directory capabilities
Create integration layer for SolidLSP language servers and diagnostics
Integrate AutogenLib for enhanced context analysis capabilities
Design multi-source context aggregation pipeline for error analysis / context enhancment / enhanced automatic error resolution / document creation / 


