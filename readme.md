# XrayDB MCP Server

Prototype of a Model Context Protocol (MCP) server that provides access to X-ray properties of elements via the [XrayDB](https://github.com/xraypy/XrayDB) library.

Cool is that this repo/server has only 2 `pip` installable dependencies:
- `mcp` for the protocol
- `xraydb` for the tool usage


So far implemented:

- xraydb.xray_edges(element)
- xraydb.guess_edge(energy, edges=used_edges)
- xraydb.xray_edge(...)
- xraydb.atomic_number(element)
- xraydb.atomic_density(element)
- xraydb.mirror_reflectivity(...)
- xraydb.multilayer_reflectivity(...)

## Showcase


More complicated multilayer reflectivity calculations are possible:

![GPT-REFL](static/gpt-mll-refl.png)


Showcased using [goose](https://github.com/block/goose/) with the free horizon-beta LLM accessed via openrouter.

![Goose Showcase](static/goose_showcase.png)

It is relatively typing error agnostic too:

![Goose Typo](static/goose_typos.png)

It can also suggest an element an corresponding edge for an energy:

![Goose guess_edge](static/goose_guess_edge.png)

It runs local using a 0.5B qwen2.5 (ca. 400MB) model with ollama: 

![Goose ollama](static/goose_ollama.png)
