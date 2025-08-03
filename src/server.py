#!/usr/bin/env python3

import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import xraydb

# Create server instance
server = Server("xraydb-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="xray_edges",
            description="Get X-ray absorption edges for an element in eV and fyields and jump ratios",
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
        ),
        types.Tool(
            name="guess_edge",
            description="Guesses the element and absorption edge based on the edge energy in eV.",
            inputSchema={
                "type": "object",
                "properties": {
                    "energy": {"type": "number", "description": "Edge energy in eV"},
                },
                "required": ["energy"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""

    if not arguments:
        raise ValueError("Missing arguments")

    try:
        if name == "xray_edges":
            element = arguments.get("element")
            if not element:
                raise ValueError("Missing element parameter")
            edges = xraydb.xray_edges(element)
            # Convert to string representation which handles the formatting
            edge_text = str(edges)
            return [
                types.TextContent(
                    type="text",
                    text=f"X-ray absorption edges for {element} with energy in eV:\n{edge_text}",
                )
            ]

        elif name == "guess_edge":
            energy = arguments.get("energy")
            if energy is None:
                raise ValueError("Missing energy parameter")

            if not isinstance(energy, (int, float)):
                raise ValueError("Energy must be a number")

            # Get elements around the edge energy
            elements = xraydb.guess_edge(energy)
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
                    text=f"Absorption edges around the energy {energy} eV, Element {element_tuple[0]} at absorption edge {element_tuple[1]}.",
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error processing {element}: {str(e)}")
        ]


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
