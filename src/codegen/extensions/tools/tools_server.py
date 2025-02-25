import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codegen.configs.models.repository import DefaultRepoConfig
from codegen.configs.models.secrets import DefaultSecrets
from codegen.extensions.langchain.tools import (
    CreateFileInput,
    CreateFileTool,
    DeleteFileInput,
    DeleteFileTool,
    EditFileInput,
    EditFileTool,
    ListDirectoryInput,
    ListDirectoryTool,
    MoveSymbolInput,
    MoveSymbolTool,
    RenameFileInput,
    RenameFileTool,
    ReplacementEditInput,
    ReplacementEditTool,
    RevealSymbolInput,
    RevealSymbolTool,
    SearchInput,
    SearchTool,
    SemanticEditInput,
    SemanticEditTool,
    ViewFileInput,
    ViewFileTool,
)
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.enums.warmup_state import WarmupState
from codegen.runner.models.apis import (
    ServerInfo,
)
from codegen.sdk.codebase.config import ProjectConfig
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

logger = logging.getLogger(__name__)

server_info: ServerInfo
codebase: Codebase


@asynccontextmanager
async def lifespan(server: FastAPI):
    global server_info
    global codebase

    try:
        server_info.warmup_state = WarmupState.PENDING
        server_info = ServerInfo(repo_name=DefaultRepoConfig.full_name or DefaultRepoConfig.name)
        logger.info(f"Starting up sandbox fastapi server for repo_name={server_info.repo_name}")
        repo_config = RepoConfig(
            name=DefaultRepoConfig.name,
            full_name=DefaultRepoConfig.full_name,
            base_dir=os.path.dirname(DefaultRepoConfig.path),
            language=ProgrammingLanguage(DefaultRepoConfig.language.upper()),
        )

        op = RepoOperator(repo_config=repo_config, access_token=DefaultSecrets.github_token, setup_option=SetupOption.PULL_OR_CLONE)
        projects = [ProjectConfig(programming_language=repo_config.language, repo_operator=op, base_path=repo_config.base_path, subdirectories=repo_config.subdirectories)]
        codebase = Codebase(projects=projects)
        server_info.warmup_state = WarmupState.COMPLETED
    except Exception:
        logger.exception("Failed to build graph during warmup")
        server_info.warmup_state = WarmupState.FAILED

    logger.info("Agent tool server is ready")
    yield
    logger.info("Shutting down agent tool server")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health() -> ServerInfo:
    return server_info


@app.post(ViewFileTool.name)
async def view_file(request: ViewFileInput) -> str:
    return await ViewFileTool().run(filepath=request.filepath, start_line=request.start_line, end_line=request.end_line, max_lines=request.max_lines, line_numbers=request.line_numbers)


@app.post(ListDirectoryTool.name)
async def directory(request: ListDirectoryInput) -> str:
    return await ListDirectoryTool.run(dirpath=request.dirpath, depth=request.depth)


@app.post(SearchTool.name)
async def search(request: SearchInput) -> str:
    return await SearchTool.run(query=request.query)


@app.post(EditFileTool.name)
async def edit_file(request: EditFileInput) -> str:
    return await EditFileTool.run(filepath=request.filepath, content=request.content)


@app.post(CreateFileTool.name)
async def create_file(request: CreateFileInput) -> str:
    return await CreateFileTool.run(filepath=request.filepath, content=request.content)


@app.post(DeleteFileTool.name)
async def delete_file(request: DeleteFileInput) -> str:
    return await DeleteFileTool.run(filepath=request.filepath)


@app.post(RenameFileTool.name)
async def rename_file(request: RenameFileInput) -> str:
    return await RenameFileTool.run(old_path=request.old_path, new_path=request.new_path)


@app.post(MoveSymbolTool.name)
async def move_symbol(request: MoveSymbolInput) -> str:
    return await MoveSymbolTool.run(symbol=request.symbol, destination=request.destination)


@app.post(RevealSymbolTool.name)
async def reveal_symbol(request: RevealSymbolInput) -> str:
    return await RevealSymbolTool.run(symbol=request.symbol)


@app.post(SemanticEditTool.name)
async def semantic_edit(request: SemanticEditInput) -> str:
    return await SemanticEditTool.run(filepath=request.filepath, edit=request.edit)


@app.post(ReplacementEditTool.name)
async def replacement_edit(request: ReplacementEditInput) -> str:
    return await ReplacementEditTool.run(filepath=request.filepath, old_code=request.old_code, new_code=request.new_code)


@app.post("get_diff")
async def get_diff(base_commit: str, head_commit: str) -> str:
    return await codebase.get_diff(base=base_commit, head=head_commit)
