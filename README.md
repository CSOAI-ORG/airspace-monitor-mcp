<div align="center">

# Airspace Monitor MCP

**MCP server for airspace monitor mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-airspace-monitor-mcp)](https://pypi.org/project/meok-airspace-monitor-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Airspace Monitor MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `check_airspace` | Check if a location/altitude is safe for drone flight. Returns restrictions, nea |
| `get_no_fly_zones` | Get all no-fly zones within a radius of a location. |
| `get_drone_regulations` | Get drone flight regulations for a country (UK, US, EU, AU, CA). |
| `plan_flight` | Plan a drone flight path and check for restrictions along the route. |

## Installation

```bash
pip install meok-airspace-monitor-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "airspace-monitor": {
      "command": "python",
      "args": ["-m", "meok_airspace_monitor_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
