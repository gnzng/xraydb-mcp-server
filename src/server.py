#!/usr/bin/env python3
import inspect
import math
from typing import List, Optional

import xraydb
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("xraydb-server")


@mcp.tool()
def xray_absorption_edges(element: str, edge: str = None) -> str:
    """
    Get X-ray absorption edges for an element or data for a specific X-ray absorption edge.

    Args:
        element (str): Element symbol (e.g., 'Fe', 'Cu') or name.
        edge (str, optional): IUPAC symbol for the edge (e.g., 'K', 'L3'). If None, returns all edges.

    Returns:
        str: Formatted string with X-ray absorption edge information.
    """
    try:
        if edge is None:
            edges = xraydb.xray_edges(element)
            if not edges:
                return f"No X-ray absorption edge data found for {element}."

            formatted_output = f"X-ray absorption edges for {element}:\n\n"
            formatted_output += (
                "Edge    Energy (eV)    Fluorescence Yield    Jump Ratio\n"
            )
            formatted_output += "-" * 55 + "\n"
            for edge_name, edge_data in edges.items():
                formatted_output += f"{edge_name:<6} {edge_data.energy:>10.1f} {edge_data.fyield:>18.6f} {edge_data.jump_ratio:>12.3f}\n"
            return formatted_output

        else:
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
def f0(ion: str, q: float) -> str:
    """
    Elastic X-ray scattering factor, f0(q), for an ion.
    Args:
        ion (str): Atomic number, symbol, or ionic symbol (e.g., 'Fe', 'Fe2+').
        q (float): Q value for scattering, q = sin(theta) / lambda, where theta=incident angle, lambda=X-ray wavelength in meters.
    Returns:
        str: Scattering factor for the given ion and Q value.
    """
    try:
        value = xraydb.f0(ion, q)
        return f"Elastic X-ray scattering factor f0 for ion '{ion}' at q={q}:\nValue: {value}"
    except Exception as e:
        return f"Error calculating f0: {str(e)}"


@mcp.tool()
def f0_ions(element: str = None) -> str:
    """
    List ion names supported in the f0() calculation. Elastic X-ray scattering factor, f0(q), for an ion.
    Args:
        element (str, optional): Element symbol, name, or atomic number. If None, returns all ions.
    Returns:
        str: List of supported ion names.
    """
    try:
        ions = xraydb.f0_ions(element=element)
        if not ions:
            return f"No ions found for element '{element}'."
        return (
            f"Supported ions for element '{element if element else 'all'}':\n"
            + ", ".join(ions)
        )
    except Exception as e:
        return f"Error retrieving f0 ions: {str(e)}"


@mcp.tool()
def chantler_data_combined(
    element: str,
    energy: float,
    data_type: str,
    incoh: bool = False,
    photo: bool = False,
    emin: float = 0.0,
    emax: float = 1e9,
    **kwargs,
) -> str:
    """
    Get various types of data from Chantler tables for a given element and energy.
    Args:
        element (str): Atomic symbol, name, or number for the element.
        energy (float): Energy in eV.
        data_type (str): Type of data to retrieve ('f1', 'f2', 'mu', 'energies').
        incoh (bool): Return only incoherent contribution (for 'mu') (default: False).
        photo (bool): Return only photo-electric contribution (for 'mu') (default: False).
        emin (float): Lower bound of energies in eV (default: 0).
        emax (float): Upper bound of energies in eV (default: 1e9).
        **kwargs: Additional keyword arguments for the underlying functions.
    Returns:
        str: Retrieved data as a formatted string.
    """
    try:
        if data_type == "f1":
            value = xraydb.f1_chantler(element, energy, **kwargs)
            return (
                f"Chantler f1 (real part) for {element} at {energy} eV:\nValue: {value}"
            )

        elif data_type == "f2":
            value = xraydb.f2_chantler(element, energy)
            return f"Chantler f2 (imaginary part) for {element} at {energy} eV:\nValue: {value}"

        elif data_type == "mu":
            value = xraydb.mu_chantler(element, energy, incoh=incoh, photo=photo)
            return f"Chantler mu/rho for {element} at {energy} eV:\nincoh: {incoh}, photo: {photo}\nmu/rho: {value} cm^2/g"

        elif data_type == "energies":
            energies = xraydb.chantler_energies(element, emin=emin, emax=emax)
            if energies is None or len(energies) == 0:
                return f"No Chantler energies found for {element} in range {emin}–{emax} eV."
            formatted = ", ".join(f"{e:.1f}" for e in energies)
            return f"Chantler tabulated energies for {element} between {emin} and {emax} eV:\n{formatted}"

        else:
            return "Invalid data type specified. Please use 'f1', 'f2', 'mu', or 'energies'."

    except Exception as e:
        return f"Error retrieving Chantler data: {str(e)}"


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


@mcp.tool()
def mu_elam(element: str, energy: float, kind: str = "total") -> str:
    """
    X-ray mass attenuation coefficient, mu/rho, for an element and energy from Elam tables.
    Args:
        element (str): Atomic number or symbol.
        energy (float): Energy in eV.
        kind (str): Type of cross-section ('total', 'photo', 'coh', 'incoh').
    Returns:
        str: mu/rho value in cm^2/g.
    """
    try:
        value = xraydb.mu_elam(element, energy, kind=kind)
        return (
            f"Elam mu/rho for {element} at {energy} eV:\n"
            f"Kind: {kind}\n"
            f"mu/rho: {value} cm^2/g"
        )
    except Exception as e:
        return f"Error retrieving Elam mu/rho: {str(e)}"


@mcp.tool()
def elam_cross_section(element: str, energy: float, cross_section_type: str) -> str:
    """
    Get coherent or incoherent scattering cross-section from Elam tables for a given element and energy.

    Args:
        element (str): Atomic number or symbol.
        energy (float): Energy in eV.
        cross_section_type (str): Type of cross-section to retrieve ('coherent' or 'incoherent').

    Returns:
        str: Cross-section value in cm^2/g as a formatted string.
    """
    try:
        if cross_section_type == "coherent":
            value = xraydb.coherent_cross_section_elam(element, energy)
            return (
                f"Elam coherent scattering cross-section for {element} at {energy} eV:\n"
                f"Value: {value} cm^2/g"
            )

        elif cross_section_type == "incoherent":
            value = xraydb.incoherent_cross_section_elam(element, energy)
            return (
                f"Elam incoherent scattering cross-section for {element} at {energy} eV:\n"
                f"Value: {value} cm^2/g"
            )

        else:
            return "Invalid cross-section type specified. Please use 'coherent' or 'incoherent'."

    except Exception as e:
        return f"Error retrieving Elam cross-section: {str(e)}"


@mcp.tool()
def xray_lines(
    element: str,
    initial_level: str = None,
    excitation_energy: float = None,
) -> str:
    """
    Get dictionary of X-ray emission lines of an element.
    Args:
        element (str): Atomic symbol, name, or number for the element.
        initial_level (str, optional): IUPAC symbol of initial level.
        excitation_energy (float, optional): Excitation energy in eV.
    Returns:
        str: Formatted string with X-ray emission lines.
    """
    try:
        lines = xraydb.xray_lines(
            element,
            initial_level=initial_level,
            excitation_energy=excitation_energy,
        )
        if not lines:
            return f"No X-ray emission lines found for {element}."

        output = f"X-ray emission lines for {element}"
        if initial_level:
            output += f", initial level: {initial_level}"
        if excitation_energy is not None:
            output += f", excitation energy: {excitation_energy} eV"
        output += ":\n\n"
        output += (
            "Siegbahn   Energy (eV)   Intensity      Initial Level   Final Level\n"
        )
        output += "-" * 65 + "\n"
        for name, line in lines.items():
            output += (
                f"{name:<9} {line.energy:>10.1f} {line.intensity:>12.6f} "
                f"{line.initial_level:>13} {line.final_level}\n"
            )
        return output
    except Exception as e:
        return f"Error retrieving X-ray emission lines: {str(e)}"


@mcp.tool()
def xray_line(element: str, line: str) -> str:
    """
    Get data for an X-ray emission line of an element, given the Siegbahn notation.
    Args:
        element (str): Atomic symbol, name, or number for the element.
        line (str): Siegbahn notation for emission line (e.g., 'Ka1', 'Lb1', 'Ka', 'La').
    Returns:
        str: Formatted string with X-ray emission line data.
    """
    try:
        result = xraydb.xray_line(element, line)
        if result is None:
            return f"Emission line '{line}' not found for element '{element}'."
        return (
            f"X-ray emission line '{line}' for {element}:\n"
            f"  Energy:        {result.energy:.1f} eV\n"
            f"  Intensity:     {result.intensity:.6f}\n"
            f"  Initial level: {result.initial_level}\n"
            f"  Final level:   {result.final_level}"
        )
    except Exception as e:
        return f"Error retrieving X-ray emission line: {str(e)}"


@mcp.tool()
def coated_reflectivity(
    coating: str,
    coating_thick: float,
    substrate: str,
    theta: float,
    energy: float,
    coating_dens: Optional[float] = None,
    surface_roughness: float = 0.0,
    substrate_dens: Optional[float] = None,
    substrate_roughness: float = 0.0,
    binder: Optional[str] = None,
    binder_thick: Optional[float] = None,
    binder_dens: Optional[float] = None,
    polarization: str = "s",
    output: str = "intensity",
) -> str:
    """
    Calculate reflectivity for a coated mirror using xraydb.coated_reflectivity.
    Args:
        coating (str): Coating material name or formula.
        coating_thick (float): Thickness of coating in Angstroms.
        substrate (str): Substrate material name or formula.
        theta (float): Mirror angle in radians.
        energy (float): X-ray energy in eV.
        coating_dens (Optional[float]): Density of mirror coating in g/cm^3.
        surface_roughness (float): Coating roughness in Angstroms.
        substrate_dens (Optional[float]): Density of substrate in g/cm^3.
        substrate_roughness (float): Substrate roughness in Angstroms.
        binder (Optional[str]): Binder material name or formula.
        binder_thick (Optional[float]): Thickness of binder in Angstroms.
        binder_dens (Optional[float]): Density of binder in g/cm^3.
        polarization (str): Mirror orientation relative to X-ray polarization.
        output (str): Output type: intensity or amplitude.
    Returns:
        str: Mirror reflectivity calculation results.
    """
    try:
        reflectivity = xraydb.coated_reflectivity(
            coating=coating,
            coating_thick=coating_thick,
            substrate=substrate,
            theta=theta,
            energy=energy,
            coating_dens=coating_dens,
            surface_roughness=surface_roughness,
            substrate_dens=substrate_dens,
            substrate_roughness=substrate_roughness,
            binder=binder,
            binder_thick=binder_thick,
            binder_dens=binder_dens,
            polarization=polarization,
            output=output,
        )
        result_type = "Intensity" if output == "intensity" else "Complex amplitude"
        return (
            f"Coated mirror reflectivity for {coating} (thickness={coating_thick} Å)"
            f"{' with binder ' + binder if binder else ''} on substrate {substrate}:\n"
            f"Theta: {theta} rad\n"
            f"Energy: {energy} eV\n"
            f"Coating density: {coating_dens if coating_dens is not None else 'default'} g/cm^3\n"
            f"Surface roughness: {surface_roughness} Å\n"
            f"Substrate density: {substrate_dens if substrate_dens is not None else 'default'} g/cm^3\n"
            f"Substrate roughness: {substrate_roughness} Å\n"
            f"Polarization: {polarization}\n"
            f"Output type: {result_type}\n"
            f"Reflectivity: {reflectivity}"
        )
    except Exception as e:
        return f"Error calculating coated mirror reflectivity: {str(e)}"


@mcp.tool()
def ionchamber_fluxes(
    gas: str = "nitrogen",
    volts: float = 1.0,
    length: float = 100.0,
    energy: float = 10000.0,
    sensitivity: float = 1e-6,
    sensitivity_units: str = "A/V",
    with_compton: bool = True,
    both_carriers: bool = True,
) -> str:
    """
    Calculate ion chamber and PIN diode fluxes for a gas or mixture.
    Args:
        gas (str): Name or formula of fill gas (default: 'nitrogen').
        volts (float): Measured voltage output of current amplifier.
        length (float): Active length of ion chamber in cm.
        energy (float): X-ray energy in eV.
        sensitivity (float): Current amplifier sensitivity.
        sensitivity_units (str): Units of current amplifier sensitivity.
        with_compton (bool): Include Compton scattering contribution.
        both_carriers (bool): Count both electron and ion current.
    Returns:
        str: Formatted string with fluxes.
    """
    try:
        result = xraydb.ionchamber_fluxes(
            gas=gas,
            volts=volts,
            length=length,
            energy=energy,
            sensitivity=sensitivity,
            sensitivity_units=sensitivity_units,
            with_compton=with_compton,
            both_carriers=both_carriers,
        )
        output = (
            f"Ion chamber fluxes for gas '{gas}' at {energy} eV, length={length} cm:\n"
            f"Incident flux:    {result.incident:.6g} Hz\n"
            f"Transmitted flux: {result.transmitted:.6g} Hz\n"
            f"Photo flux:       {result.photo:.6g} Hz\n"
            f"Incoherent flux:  {result.incoherent:.6g} Hz\n"
            f"Coherent flux:    {getattr(result, 'coherent', 0.0):.6g} Hz"
        )
        return output
    except Exception as e:
        return f"Error calculating ion chamber fluxes: {str(e)}"


@mcp.tool()
def dynamical_theta_offset(
    energy: float,
    crystal: str = "Si",
    hkl: tuple = (1, 1, 1),
    a: float = None,
    m: int = 1,
    polarization: str = "s",
) -> str:
    """
    Angular offset from Bragg diffraction for a perfect single crystal.
    Args:
        energy (float): X-ray energy in eV
        crystal (str): Name of crystal ('Si', 'Ge', or 'C')
        hkl (tuple): h, k, l for reflection
        a (float or None): Lattice constant (Angstroms)
        m (int): Order of reflection
        polarization (str): 's', 'p', 'u', or None
    Returns:
        str: Theta offset in radians
    """
    try:
        theta_offset = xraydb.dynamical_theta_offset(
            energy, crystal=crystal, hkl=hkl, a=a, m=m, polarization=polarization
        )
        return f"Theta offset: {theta_offset:.8g} radians"
    except Exception as e:
        return f"Error calculating dynamical theta offset: {str(e)}"


@mcp.tool()
def transmission_sample(
    sample: "str | dict",
    energy: float,
    absorp_total: float = 2.6,
    area: float = 1.0,
    density: Optional[float] = None,
    frac_type: str = "mass",
) -> str:
    """
    Analyze transmission mode sample.

    Args:
        sample (str or dict): Chemical formula or mass fractions. One entry can be -1 for unspecified portion.
        energy (float): X-ray energy (eV) at which transmission will be analyzed. Recommended: edge energy + 50 eV.
        absorp_total (float): Total absorption (mu_t*d) at specified energy.
        area (float, optional): Area (cm^2) of the sample. Default: 1 cm^2.
        density (float, optional): Density (g/cm^3) of the sample.
        frac_type (str, optional): 'mass' or 'molar'. Specifies type of fractions if sample is dict.

    Returns:
        str: Dictionary fields include:
            - energy(eV): incident energy
            - absorp_total: total absorption
            - mass_fractions: mass fractions of elements
            - molar_fractions: molar fractions of elements
            - absorbance_steps: absorbance steps for each element
            - area (cm^2): area, if specified
            - mass_total(mg): total mass, if area specified
            - mass_components(mg): mass of each element, if area specified
            - density(g/cc): density, if specified
            - thickness(mm): thickness, if area and density specified
            - absorption_length(um): absorption length, if area and density specified
    """
    try:
        result = xraydb.transmission_sample(
            sample,
            energy,
            absorp_total=absorp_total,
            area=area,
            density=density,
            frac_type=frac_type,
        )
        return str(result)
    except Exception as e:
        return f"Error analyzing transmission sample: {str(e)}"


@mcp.tool()
def formula_to_mass_fracs(formula: "str | dict") -> dict:
    """
    Calculate mass fractions of elements from a given molecular formula.

    Args:
        formula (str or dict): Chemical formula.

    Returns:
        dict: Fields of each element and values of their mass fractions.
    """
    return xraydb.formula_to_mass_fracs(formula)


@mcp.tool()
def mass_fracs_to_molar_fracs(mass_fracs: dict) -> dict:
    """
    Calculate molar fractions from a given mass fractions of elements.
    Result is normalized to one.

    Args:
        mass_fracs (dict): Mass fractions of elements.

    Returns:
        dict: Fields of each element and values of their coefficients.
    """
    return xraydb.mass_fracs_to_molar_fracs(mass_fracs)


@mcp.tool()
def validate_mass_fracs(mass_fracs: dict) -> dict:
    """
    Validate mass fractions. Either verify they sum to one, or calculate
    the remaining portion of a compound/element with value specified as -1.

    Additionally, compounds specified in mass_fracs will be separated to the
    individual elements.

    Args:
        mass_fracs (dict): Mass fractions of elements.

    Returns:
        dict: Validated and simplified mass fractions.
    """
    return xraydb._validate_mass_fracs(mass_fracs)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
