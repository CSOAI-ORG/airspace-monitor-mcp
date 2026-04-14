#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("airspace-monitor-mcp")
@mcp.tool(name="check_airspace")
async def check_airspace(latitude: float, longitude: float, altitude_m: float, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    restricted = abs(latitude - 51.5) < 0.1 and abs(longitude - (-0.1)) < 0.1
    return {"lat": latitude, "lon": longitude, "altitude_m": altitude_m, "restricted": restricted, "clearance": not restricted and altitude_m <= 120}
@mcp.tool(name="no_fly_zones")
async def no_fly_zones(region: str, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    zones = {"london": [{"lat": 51.5, "lon": -0.1, "radius_km": 5}], "heathrow": [{"lat": 51.47, "lon": -0.46, "radius_km": 2}]}
    return {"region": region, "zones": zones.get(region.lower(), [])}
if __name__ == "__main__":
    mcp.run()
