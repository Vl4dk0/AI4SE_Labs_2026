# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2,<2", "pydantic>=2"]
# ///
"""Local MCP server (stdio) with one tool: a D&D dice roller."""

import random
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, validate_call

mcp = FastMCP("dice")


class RollResult(BaseModel):
    rolls: list[int]
    modifier: int
    total: int


@mcp.tool()
@validate_call
def roll_dice(
    count: Annotated[int, Field(ge=1, le=100, description="Number of dice")],
    sides: Annotated[
        Literal[4, 6, 8, 10, 12, 20, 100], Field(description="Sides per die")
    ],
    modifier: Annotated[int, Field(ge=-100, le=100, description="Added to sum")] = 0,
) -> RollResult:
    """Roll `count` dice with `sides` sides and add `modifier` (e.g. 3d6+2)."""
    rolls = [random.randint(1, sides) for _ in range(count)]
    return RollResult(rolls=rolls, modifier=modifier, total=sum(rolls) + modifier)


if __name__ == "__main__":
    mcp.run(transport="stdio")
