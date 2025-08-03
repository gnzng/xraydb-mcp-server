# XrayDB MCP Server

Prototype of a Model Context Protocol (MCP) server that provides access to X-ray properties of elements via the [XrayDB](https://github.com/xraypy/XrayDB) library.

Cool is that this repo/server has only 2 `pip` installable dependencies:
- `mcp` for the protocol
- `xraydb` for the tool usage


So far implemented:
- `xraydb.xray_edges(element)` 

## Showcase

Showcased using [goose](https://github.com/block/goose/) with the free horizon-beta LLM accessed via openrouter.

![Goose Showcase](static/goose_showcase.png)

It is relatively typing error agnostic too:

![Goose Tyoi](static/goose_typos.png)

