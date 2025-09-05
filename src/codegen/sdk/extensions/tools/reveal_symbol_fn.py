from logging import getLogger
from typing import Annotated

from codegen.sdk.extensions.tools.reveal_symbol import reveal_symbol

logger = getLogger(__name__)


class RevealSymbolInput(BaseModel):
    """Input for revealing symbol relationships."""

    symbol_name: str = Field(..., description="Name of the symbol to analyze")
    degree: int = Field(
        default=1, description="How many degrees of separation to traverse"
    )
    max_tokens: int | None = Field(
        default=None,
        description="Optional maximum number of tokens for all source code combined",
    )
    collect_dependencies: bool = Field(
        default=True, description="Whether to collect dependencies"
    )
    collect_usages: bool = Field(default=True, description="Whether to collect usages")


class RevealSymbolTool(BaseTool):
    """Tool for revealing symbol relationships."""

    name: ClassVar[str] = "reveal_symbol"
    description: ClassVar[str] = (
        "Reveal the dependencies and usages of a symbol up to N degrees"
    )
    args_schema: ClassVar[type[BaseModel]] = RevealSymbolInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        symbol_name: str,
        degree: int = 1,
        max_tokens: int | None = None,
        collect_dependencies: bool = True,
        collect_usages: bool = True,
    ) -> str:
        result = reveal_symbol(
            codebase=self.codebase,
            symbol_name=symbol_name,
            max_depth=degree,
            max_tokens=max_tokens,
            collect_dependencies=collect_dependencies,
            collect_usages=collect_usages,
        )
        return result.render()


@mcp.tool(
    name="reveal_symbol",
    description="Shows all usages + dependencies of the provided symbol, up to the specified max depth (e.g. show 2nd-level usages/dependencies)",
)
async def reveal_symbol_fn(
    symbol: Annotated[str, "symbol to show usages and dependencies for"],
    filepath: Annotated[str, "file path to the target file to split"] = None,
    max_depth: Annotated[int, "maximum depth to show dependencies"] = 1,
):
    codebase = state.parsed_codebase
    output = reveal_symbol(
        codebase=codebase,
        symbol_name=symbol,
        filepath=filepath,
        max_depth=max_depth,
        max_tokens=10000,
    )
    return output
