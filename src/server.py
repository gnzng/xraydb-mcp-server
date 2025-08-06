#!/usr/bin/env python3
import math

import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import xraydb
import inspect


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


@register_tool(
    name="atomic_number",
    description="Return the atomic number Z for an element.",
    inputSchema={
        "type": "object",
        "properties": {
            "element": {
                "type": "string",
                "description": "Element symbol (e.g., 'Fe', 'Cu') or name",
            },
        },
        "required": ["element"],
    },
)
async def tool_atomic_number(arguments):
    element = arguments.get("element")
    if not element:
        raise ValueError("Missing element parameter")
    atomic_number = xraydb.atomic_number(element)
    if atomic_number is None:
        return [
            types.TextContent(
                type="text",
                text=f"Unknown element: {element}",
            )
        ]
    return [
        types.TextContent(
            type="text",
            text=f"Atomic number of {element.capitalize()} is {atomic_number}.",
        )
    ]


@register_tool(
    name="atomic_density",
    description="Return the atomic density (gr/cm^3) for an element. Given element symbol (e.g., 'Fe', 'Cu').",
    inputSchema={
        "type": "object",
        "properties": {
            "element": {
                "type": "string",
                "description": "Element symbol (e.g., 'Fe', 'Cu') or name",
            },
        },
        "required": ["element"],
    },
)
async def tool_atomic_density(arguments):
    element = arguments.get("element")
    if not element:
        raise ValueError("Missing element parameter")
    atomic_density = xraydb.atomic_density(element)
    if atomic_density is None:
        return [
            types.TextContent(
                type="text",
                text=f"Unknown element: {element}",
            )
        ]
    return [
        types.TextContent(
            type="text",
            text=f"Atomic density of {element.capitalize()} is {atomic_density:.2f} g/cm^3.",
        )
    ]


@register_tool(
    name="mirror_reflectivity",
    description="Calculate mirror reflectivity for a thick, single-layer mirror.",
    inputSchema={
        "type": "object",
        "properties": {
            "formula": {
                "type": "string",
                "description": "Material name or formula (e.g., 'Si', 'Rh', 'silicon')",
            },
            "theta": {
                "type": "number",
                "description": "Mirror angle in radians",
            },
            "energy": {
                "type": "number",
                "description": "X-ray energy in eV",
            },
            "density": {
                "type": ["number", "null"],
                "description": "Material density in g/cm^3 (optional)",
                "default": None,
            },
            "roughness": {
                "type": "number",
                "description": "Mirror roughness in Angstroms (default: 0.0)",
                "default": 0.0,
            },
            "polarization": {
                "type": "string",
                "enum": ["s", "p"],
                "description": "Mirror orientation relative to X-ray polarization (default: 's')",
                "default": "s",
            },
            "output": {
                "type": "string",
                "enum": ["intensity", "amplitude"],
                "description": "Output type: intensity or complex amplitude (default: 'intensity')",
                "default": "intensity",
            },
        },
        "required": ["formula", "theta", "energy"],
    },
)
async def tool_mirror_reflectivity(arguments):
    formula = arguments.get("formula")
    theta = arguments.get("theta")
    energy = arguments.get("energy")
    density = arguments.get("density", None)
    roughness = arguments.get("roughness", 0.0)
    polarization = arguments.get("polarization", "s")
    output = arguments.get("output", "intensity")

    if formula is None or theta is None or energy is None:
        raise ValueError("Missing required parameters: formula, theta, or energy")

    try:
        sig = inspect.signature(xraydb.mirror_reflectivity)
        if (
            "output" in sig.parameters
            and sig.parameters["output"].kind == inspect.Parameter.KEYWORD_ONLY
        ):
            # output is keyword-only
            reflectivity = xraydb.mirror_reflectivity(
                formula,
                theta,
                energy,
                density=density,
                roughness=roughness,
                polarization=polarization,
                output=output,
            )
        elif "output" in sig.parameters:
            # output is positional or can be keyword
            reflectivity = xraydb.mirror_reflectivity(
                formula, theta, energy, density, roughness, polarization, output
            )
        else:
            # fallback: don't pass output
            reflectivity = xraydb.mirror_reflectivity(
                formula, theta, energy, density, roughness, polarization
            )
        if reflectivity is None:
            return [
                types.TextContent(
                    type="text",
                    text=(
                        "Error calculating mirror reflectivity: No result returned. "
                        "This may be due to an invalid material formula, density, or other input. "
                        f"Inputs: formula={formula}, theta={theta}, energy={energy}, density={density}, roughness={roughness}, polarization={polarization}, output={output}"
                    ),
                )
            ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error calculating mirror reflectivity: {str(e)}",
            )
        ]

    result_type = "Intensity" if output == "intensity" else "Complex amplitude"
    return [
        types.TextContent(
            type="text",
            text=(
                f"Mirror reflectivity for {formula} at theta={theta} rad, energy={energy} eV:\n"
                f"Density: {density if density is not None else 'default'} g/cm^3\n"
                f"Roughness: {roughness} Å\n"
                f"Polarization: {polarization}\n"
                f"Output type: {result_type}\n"
                f"Reflectivity: {reflectivity}"
            ),
        )
    ]


@register_tool(
    name="multilayer_reflectivity",
    description=(
        "Calculate reflectivity for a multilayer mirror stack. "
        "Given a stackup (list of material formulas, e.g., ['Mo', 'Si']), thicknesses (list of layer thicknesses in Angstroms), "
        "and substrate (material name or formula), computes the X-ray reflectivity for a multilayer mirror. "
        "Supports specifying the number of periods (n_periods), densities for each layer (density, optional), substrate density (optional), "
        "substrate and surface roughness (in Angstroms), polarization ('s' or 'p'), and output type ('intensity' or 'amplitude'). "
        "Only one of theta or energy can be an array. Densities can be None for known materials or a list matching the stackup. "
        "Polarization 's' means X-ray polarization along the mirror surface (vertically deflecting), 'p' means normal to the surface (horizontally deflecting)."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "stackup": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of material formulas for the multilayer stack (e.g., ['Mo', 'Si']). "
                    "Each entry should be a valid material name or chemical formula."
                ),
            },
            "thickness": {
                "type": "array",
                "items": {"type": "number"},
                "description": (
                    "List of layer thicknesses in Angstroms, one per material in stackup. "
                    "Length must match stackup."
                ),
            },
            "substrate": {
                "type": "string",
                "description": (
                    "Substrate material name or formula (e.g., 'Si', 'silicon'). "
                    "Used as the base layer for the mirror."
                ),
            },
            "theta": {
                "type": "number",
                "description": (
                    "Mirror angle in radians. Only one of theta or energy can be an array."
                ),
            },
            "energy": {
                "type": "number",
                "description": (
                    "X-ray energy in eV. Only one of theta or energy can be an array."
                ),
            },
            "n_periods": {
                "type": "integer",
                "description": (
                    "Number of periods in the multilayer stack (default: 1). "
                    "Each period repeats the stackup and thickness sequence."
                ),
                "default": 1,
            },
            "density": {
                "type": ["array", "null"],
                "items": {"type": "number"},
                "description": (
                    "Material densities in g/cm^3 for each layer in stackup (optional). "
                    "If None, uses default density for known materials. "
                    "Length must match stackup."
                ),
                "default": None,
            },
            "substrate_density": {
                "type": ["number", "null"],
                "description": (
                    "Density of substrate in g/cm^3 (optional). "
                    "If None, uses default density for known substrate materials."
                ),
                "default": None,
            },
            "substrate_rough": {
                "type": "number",
                "description": (
                    "Substrate roughness in Angstroms (default: 0.0). "
                    "Affects reflectivity at the substrate interface."
                ),
                "default": 0.0,
            },
            "surface_rough": {
                "type": "number",
                "description": (
                    "Surface roughness in Angstroms (default: 0.0). "
                    "Affects reflectivity at the top surface."
                ),
                "default": 0.0,
            },
            "polarization": {
                "type": "string",
                "enum": ["s", "p"],
                "description": (
                    "Mirror orientation relative to X-ray polarization (default: 's'). "
                    "'s': polarization along mirror surface (vertically deflecting); "
                    "'p': polarization normal to surface (horizontally deflecting)."
                ),
                "default": "s",
            },
            "output": {
                "type": "string",
                "enum": ["intensity", "amplitude"],
                "description": (
                    "Output type: 'intensity' for reflectivity values, "
                    "'amplitude' for complex amplitude (default: 'intensity')."
                ),
                "default": "intensity",
            },
        },
        "required": ["stackup", "thickness", "substrate", "theta", "energy"],
    },
)
async def tool_multilayer_reflectivity(arguments):
    stackup = arguments.get("stackup")
    thickness = arguments.get("thickness")
    substrate = arguments.get("substrate")
    theta = arguments.get("theta")
    energy = arguments.get("energy")
    n_periods = arguments.get("n_periods", 1)
    density = arguments.get("density", None)
    substrate_density = arguments.get("substrate_density", None)
    substrate_rough = arguments.get("substrate_rough", 0.0)
    surface_rough = arguments.get("surface_rough", 0.0)
    polarization = arguments.get("polarization", "s")
    output = arguments.get("output", "intensity")

    # Validate required arguments
    if not (isinstance(stackup, list) and isinstance(thickness, list)):
        raise ValueError("stackup and thickness must be lists")
    if len(stackup) != len(thickness):
        raise ValueError("stackup and thickness must be the same length")

    try:
        reflectivity = xraydb.multilayer_reflectivity(
            stackup,
            thickness,
            substrate,
            theta,
            energy,
            n_periods=n_periods,
            density=density,
            substrate_density=substrate_density,
            substrate_rough=substrate_rough,
            surface_rough=surface_rough,
            polarization=polarization,
            output=output,
        )
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error calculating multilayer reflectivity: {str(e)}",
            )
        ]

    result_type = "Intensity" if output == "intensity" else "Complex amplitude"
    return [
        types.TextContent(
            type="text",
            text=(
                f"Multilayer reflectivity for stackup {stackup} with thicknesses {thickness} Å, "
                f"substrate={substrate}, theta={theta} rad, energy={energy} eV:\n"
                f"n_periods: {n_periods}\n"
                f"Density: {density if density is not None else 'default'}\n"
                f"Substrate density: {substrate_density if substrate_density is not None else 'default'}\n"
                f"Substrate roughness: {substrate_rough} Å\n"
                f"Surface roughness: {surface_rough} Å\n"
                f"Polarization: {polarization}\n"
                f"Output type: {result_type}\n"
                f"Reflectivity: {reflectivity}"
            ),
        )
    ]


@register_tool(
    name="material_mu",
    description="X-ray attenuation length (in 1/cm) for a material by name or formula. Uses mu_elam().",
    inputSchema={
        "type": "object",
        "properties": {
            "name_or_formula": {
                "type": "string",
                "description": "Chemical formula or material name (e.g., 'H2O', 'Si', 'silicon').",
            },
            "energy": {
                "type": "number",
                "description": "X-ray energy in eV.",
            },
            "density": {
                "type": ["number", "null"],
                "description": "Material density in g/cm^3 (optional). If None, uses default for known materials.",
                "default": None,
            },
            "kind": {
                "type": "string",
                "enum": ["photo", "total"],
                "description": "Return photo-absorption or total cross-section ('total' by default).",
                "default": "total",
            },
        },
        "required": ["name_or_formula", "energy"],
    },
)
async def tool_material_mu(arguments):
    name_or_formula = arguments.get("name_or_formula")
    energy = arguments.get("energy")
    density = arguments.get("density", None)
    kind = arguments.get("kind", "total")
    if name_or_formula is None or energy is None:
        raise ValueError("Missing required parameters: name_or_formula or energy")
    try:
        mu = xraydb.material_mu(name_or_formula, energy, density=density, kind=kind)
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error calculating material_mu: {str(e)}",
            )
        ]
    return [
        types.TextContent(
            type="text",
            text=(
                f"X-ray attenuation length (mu) for material '{name_or_formula}' at {energy} eV:\n"
                f"Density: {density if density is not None else 'default'} g/cm^3\n"
                f"Kind: {kind}\n"
                f"mu: {mu:.6f} 1/cm"
            ),
        )
    ]


@register_tool(
    name="lambert_beer",
    description="Calculate X-ray transmission using the Lambert-Beer law: I = I0 * exp(-mu * thickness).",
    inputSchema={
        "type": "object",
        "properties": {
            "mu": {
                "type": "number",
                "description": "Linear attenuation coefficient (mu) in 1/cm.",
            },
            "thickness": {
                "type": "number",
                "description": "Sample thickness in cm.",
            },
            "I0": {
                "type": "number",
                "description": "Incident intensity (optional, default: 1.0).",
                "default": 1.0,
            },
        },
        "required": ["mu", "thickness"],
    },
)
async def tool_lambert_beer(arguments):
    mu = arguments.get("mu")
    thickness = arguments.get("thickness")
    I0 = arguments.get("I0", 1.0)
    if mu is None or thickness is None:
        raise ValueError("Missing required parameters: mu or thickness")
    transmission = I0 * math.exp(-mu * thickness)
    return [
        types.TextContent(
            type="text",
            text=(
                f"Lambert-Beer law calculation:\n"
                f"mu = {mu} 1/cm\n"
                f"thickness = {thickness} cm\n"
                f"I0 = {I0}\n"
                f"Transmitted intensity (I): {transmission:.6g}"
            ),
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
