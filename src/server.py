#!/usr/bin/env python3

import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import xraydb

# Create server instance
server = Server("xraydb-server")

# Tool registry: name -> dict with description, inputSchema, handler
TOOL_REGISTRY = {}


def register_tool(name, description, inputSchema):
    def decorator(func):
        TOOL_REGISTRY[name] = {
            "description": description,
            "inputSchema": inputSchema,
            "handler": func,
        }
        return func

    return decorator


# Register tools systematically
@register_tool(
    name="xray_edges",
    description="Get X-ray absorption edges for an element in eV.",
    inputSchema={
        "type": "object",
        "properties": {
            "element": {
                "type": "string",
                "description": "Element symbol (e.g., 'Fe', 'Cu') or name",
            }
        },
        "required": ["element"],
    },
)
async def tool_xray_edges(arguments):
    element = arguments.get("element")
    if not element:
        raise ValueError("Missing element parameter")
    edges = xraydb.xray_edges(element)
    formatted_output = f"X-ray absorption edges for {element.capitalize()}:\n\n"
    formatted_output += "Edge    Energy (eV)    Fluorescence Yield    Jump Ratio\n"
    formatted_output += "-" * 55 + "\n"
    for edge_name, edge_data in edges.items():
        formatted_output += f"{edge_name:<6} {edge_data.energy:>10.1f} {edge_data.fyield:>18.6f} {edge_data.jump_ratio:>12.3f}\n"
    return [
        types.TextContent(
            type="text",
            text=formatted_output,
        )
    ]


@register_tool(
    name="guess_edge",
    description="Guesses the element and absorption edge based on the edge energy in eV.",
    inputSchema={
        "type": "object",
        "properties": {
            "energy": {"type": "number", "description": "Edge energy in eV"},
        },
        "required": ["energy"],
    },
)
async def tool_guess_edge(arguments):
    energy = arguments.get("energy")
    if energy is None:
        raise ValueError("Missing energy parameter")
    if not isinstance(energy, (int, float)):
        raise ValueError("Energy must be a number")
    used_edges = ("K", "L3", "L2", "L1", "M4", "M5")
    elements = xraydb.guess_edge(energy, edges=used_edges)
    if not elements:
        return [
            types.TextContent(
                type="text",
                text=f"No elements found around the edge energy {energy} eV.",
            )
        ]
    element_tuple = elements
    return [
        types.TextContent(
            type="text",
            text=f"Absorption edge near {energy} eV:\n\n"
            + f"Element: {element_tuple[0].capitalize()}\n"
            + f"Edge: {element_tuple[1]}\n"
            + f"Exact energy: {xraydb.xray_edge(element_tuple[0], element_tuple[1]).energy:.1f} eV\n"
            + f"Looked for absorption edges: {', '.join(used_edges)}\n",
        )
    ]


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools systematically."""
    return [
        types.Tool(
            name=name,
            description=tool["description"],
            inputSchema=tool["inputSchema"],
        )
        for name, tool in TOOL_REGISTRY.items()
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Systematic tool call dispatcher."""
    if not arguments:
        raise ValueError("Missing arguments")
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    try:
        return await tool["handler"](arguments)
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error processing: {str(e)}")]


async def main():
    # Run the server using stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="xraydb-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
