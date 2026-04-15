# Airspace Monitor MCP Server

> By [MEOK AI Labs](https://meok.ai) — Drone/aircraft airspace compliance, no-fly zones, and flight planning

## Installation

```bash
pip install airspace-monitor-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install airspace-monitor-mcp
```

## Tools

### `check_airspace`
Check if a location/altitude is safe for drone flight. Returns restrictions, nearby zones, and clearance status.

**Parameters:**
- `latitude` (float): Latitude
- `longitude` (float): Longitude
- `altitude_m` (float): Altitude in meters (default 120)

### `get_no_fly_zones`
Get all no-fly zones within a radius of a location. Includes airports, security zones, and critical infrastructure.

**Parameters:**
- `latitude` (float): Center latitude
- `longitude` (float): Center longitude
- `radius_km` (float): Search radius in km (default 50)

### `get_drone_regulations`
Get drone flight regulations for a country (UK, US, EU, AU, CA). Returns altitude limits, licensing, and registration requirements.

**Parameters:**
- `country` (str): Country code (default 'UK')

### `plan_flight`
Plan a drone flight path and check for restrictions along the route. Returns distance, time estimate, and conflicts.

**Parameters:**
- `start_lat` (float): Start latitude
- `start_lon` (float): Start longitude
- `end_lat` (float): End latitude
- `end_lon` (float): End longitude
- `altitude_m` (float): Flight altitude in meters (default 100)

## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
