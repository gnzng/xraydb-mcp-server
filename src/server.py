#!/usr/bin/env python3
import xraydb
from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import inspect
import math

mcp = FastMCP("xraydb-server")


@mcp.tool()
def xray_edges(element: str) -> str:
    """
    Get X-ray absorption edges for an element.
    Args:
        element (str): Element symbol (e.g., 'Fe', 'Cu') or name.
    Returns:
        str: Formatted string with X-ray absorption edges information.
    """
    try:
        edges = xraydb.xray_edges(element)
        if not edges:
            return f"No X-ray absorption edge data found for {element}."

        formatted_output = f"X-ray absorption edges for {element}:\n\n"
        formatted_output += "Edge    Energy (eV)    Fluorescence Yield    Jump Ratio\n"
        formatted_output += "-" * 55 + "\n"
        for edge_name, edge_data in edges.items():
            formatted_output += f"{edge_name:<6} {edge_data.energy:>10.1f} {edge_data.fyield:>18.6f} {edge_data.jump_ratio:>12.3f}\n"
        return formatted_output
    except ValueError as e:
        return str(e)


@mcp.tool()
def xray_edge(element: str, edge: str) -> str:
    """
    Get data for a specific X-ray absorption edge.
    Args:
        element (str): Element symbol (e.g., 'Fe', 'Cu') or name.
        edge (str): IUPAC symbol for the edge (e.g., 'K', 'L3').
    Returns:
        str: Formatted string with the specific X-ray edge information.
    """
    try:
        edge_data = xraydb.xray_edge(element, edge)
        if edge_data is None:
            return f"Edge '{edge.upper()}' not found for element '{element}'."

        output = f"X-ray Edge Data for {element}, {edge.upper()} edge:\n"
        output += f"  Absorption Edge Energy: {edge_data.energy:.1f} eV\n"
        output += f"  Fluorescence Yield:     {edge_data.fyield:.6f}\n"
        output += f"  Jump Ratio:             {edge_data.jump_ratio:.3f}"
        return output
    except ValueError as e:
        return str(e)


@mcp.tool()
def guess_edge(
    energy: float, edges: tuple = ("K", "L3", "L2", "L1", "M4", "M5")
) -> str:
    """
    Guesses the element and absorption edge based on the edge energy in eV.
    Args:
        energy (float): Edge energy in eV.
        edges (tuple): Tuple of edge labels to consider (default: ("K", "L3", "L2", "L1", "M4", "M5")).
    Returns:
        str: Information about the element and absorption edge.
    """
    if not isinstance(energy, (int, float)):
        raise ValueError("Energy must be a number")

    used_edges = edges
    elements = xraydb.guess_edge(energy, edges=used_edges)

    if not elements:
        return f"No elements found around the edge energy {energy} eV."

    element_tuple = elements
    exact_energy = xraydb.xray_edge(element_tuple[0], element_tuple[1]).energy

    return (
        f"Absorption edge near {energy} eV:\n\n"
        f"Element: {element_tuple[0].capitalize()}\n"
        f"Edge: {element_tuple[1]}\n"
        f"Exact energy: {exact_energy:.1f} eV\n"
        f"Looked for absorption edges: {', '.join(used_edges)}"
    )


@mcp.tool()
def atomic_number(element: str) -> str:
    """
    Return the atomic number Z for an element.
    Args:
        element (str): Element symbol (e.g., 'Fe', 'Cu') or name.
    Returns:
        str: Atomic number information.
    """
    if not element:
        raise ValueError("Missing element parameter")

    atomic_num = xraydb.atomic_number(element)
    if atomic_num is None:
        return f"Unknown element: {element}"

    return f"Atomic number of {element.capitalize()} is {atomic_num}."


@mcp.tool()
def atomic_density(element: str) -> str:
    """
    Return the atomic density (gr/cm^3) for an element.
    Args:
        element (str): Element symbol (e.g., 'Fe', 'Cu') or name.
    Returns:
        str: Atomic density information.
    """
    if not element:
        raise ValueError("Missing element parameter")

    density = xraydb.atomic_density(element)
    if density is None:
        return f"Unknown element: {element}"

    return f"Atomic density of {element.capitalize()} is {density:.2f} g/cm^3."


@mcp.tool()
def mirror_reflectivity(
    formula: str,
    theta: float,
    energy: float,
    density: Optional[float] = None,
    roughness: float = 0.0,
    polarization: str = "s",
    output: str = "intensity",
) -> str:
    """
    Calculate mirror reflectivity for a thick, single-layer mirror.
    Args:
        formula (str): Material name or formula (e.g., 'Si', 'Rh', 'silicon').
        theta (float): Mirror angle in radians.
        energy (float): X-ray energy in eV.
        density (Optional[float]): Material density in g/cm^3 (optional).
        roughness (float): Mirror roughness in Angstroms (default: 0.0).
        polarization (str): Mirror orientation relative to X-ray polarization (default: 's').
        output (str): Output type: intensity or amplitude (default: 'intensity').
    Returns:
        str: Mirror reflectivity calculation results.
    """
    try:
        sig = inspect.signature(xraydb.mirror_reflectivity)
        if (
            "output" in sig.parameters
            and sig.parameters["output"].kind == inspect.Parameter.KEYWORD_ONLY
        ):
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
            reflectivity = xraydb.mirror_reflectivity(
                formula, theta, energy, density, roughness, polarization, output
            )
        else:
            reflectivity = xraydb.mirror_reflectivity(
                formula, theta, energy, density, roughness, polarization
            )

        if reflectivity is None:
            return (
                "Error calculating mirror reflectivity: No result returned. "
                "This may be due to an invalid material formula, density, or other input. "
                f"Inputs: formula={formula}, theta={theta}, energy={energy}, density={density}, "
                f"roughness={roughness}, polarization={polarization}, output={output}"
            )
    except Exception as e:
        return f"Error calculating mirror reflectivity: {str(e)}"

    result_type = "Intensity" if output == "intensity" else "Complex amplitude"
    return (
        f"Mirror reflectivity for {formula} at theta={theta} rad, energy={energy} eV:\n"
        f"Density: {density if density is not None else 'default'} g/cm^3\n"
        f"Roughness: {roughness} Å\n"
        f"Polarization: {polarization}\n"
        f"Output type: {result_type}\n"
        f"Reflectivity: {reflectivity}"
    )


@mcp.tool()
def multilayer_reflectivity(
    stackup: List[str],
    thickness: List[float],
    substrate: str,
    theta: float,
    energy: float,
    n_periods: int = 1,
    density: Optional[List[float]] = None,
    substrate_density: Optional[float] = None,
    substrate_rough: float = 0.0,
    surface_rough: float = 0.0,
    polarization: str = "s",
    output: str = "intensity",
) -> str:
    """
    Calculate reflectivity for a multilayer mirror stack.
    Args:
        stackup (List[str]): List of material formulas for the multilayer stack.
        thickness (List[float]): List of layer thicknesses in Angstroms.
        substrate (str): Substrate material name or formula.
        theta (float): Mirror angle in radians.
        energy (float): X-ray energy in eV.
        n_periods (int): Number of periods in the multilayer stack (default: 1).
        density (Optional[List[float]]): Material densities in g/cm^3 for each layer (optional).
        substrate_density (Optional[float]): Density of substrate in g/cm^3 (optional).
        substrate_rough (float): Substrate roughness in Angstroms (default: 0.0).
        surface_rough (float): Surface roughness in Angstroms (default: 0.0).
        polarization (str): Mirror orientation relative to X-ray polarization (default: 's').
        output (str): Output type: 'intensity' or 'amplitude' (default: 'intensity').
    Returns:
        str: Multilayer reflectivity calculation results.
    """
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
        return f"Error calculating multilayer reflectivity: {str(e)}"

    result_type = "Intensity" if output == "intensity" else "Complex amplitude"
    return (
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
    )


@mcp.tool()
def material_mu(
    name_or_formula: str,
    energy: float,
    density: Optional[float] = None,
    kind: str = "total",
) -> str:
    """
    X-ray attenuation length (in 1/cm) for a material by name or formula.
    Args:
        name_or_formula (str): Chemical formula or material name.
        energy (float): X-ray energy in eV.
        density (Optional[float]): Material density in g/cm^3 (optional).
        kind (str): Return photo-absorption or total cross-section ('total' by default).
    Returns:
        str: X-ray attenuation length information.
    """
    try:
        mu = xraydb.material_mu(name_or_formula, energy, density=density, kind=kind)
    except Exception as e:
        return f"Error calculating material_mu: {str(e)}"

    return (
        f"X-ray attenuation length (mu) for material '{name_or_formula}' at {energy} eV:\n"
        f"Density: {density if density is not None else 'default'} g/cm^3\n"
        f"Kind: {kind}\n"
        f"mu: {mu:.6f} 1/cm"
    )


@mcp.tool()
def lambert_beer(mu: float, thickness: float, I0: float = 1.0) -> str:
    """
    Calculate X-ray transmission using the Lambert-Beer law: I = I0 * exp(-mu * thickness).
    Args:
        mu (float): Linear attenuation coefficient (mu) in 1/cm.
        thickness (float): Sample thickness in cm.
        I0 (float): Incident intensity (optional, default: 1.0).
    Returns:
        str: Lambert-Beer law calculation results.
    """
    transmission = I0 * math.exp(-mu * thickness)
    return (
        f"Lambert-Beer law calculation:\n"
        f"mu = {mu} 1/cm\n"
        f"thickness = {thickness} cm\n"
        f"I0 = {I0}\n"
        f"Transmitted intensity (I): {transmission:.6g}"
    )


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
