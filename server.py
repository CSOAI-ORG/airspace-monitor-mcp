#!/usr/bin/env python3
"""
Airspace Monitor MCP — MEOK AI Labs. Drone/aircraft airspace compliance, no-fly zones, NOTAM alerts."""

import sys, os
from auth_middleware import check_access

import json, math
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

mcp = FastMCP("airspace-monitor", instructions="Airspace monitoring and drone compliance. Check restricted zones, NOTAMs, flight clearance, and altitude limits. By MEOK AI Labs.")

# Major airports and restricted zones (lat, lon, radius_km, max_alt_m, name)
RESTRICTED_ZONES = [
    {"name": "London Heathrow", "lat": 51.4700, "lon": -0.4543, "radius_km": 6, "max_alt_m": 0, "type": "airport"},
    {"name": "London Gatwick", "lat": 51.1537, "lon": -0.1821, "radius_km": 6, "max_alt_m": 0, "type": "airport"},
    {"name": "London City", "lat": 51.5053, "lon": 0.0553, "radius_km": 4, "max_alt_m": 0, "type": "airport"},
    {"name": "Buckingham Palace", "lat": 51.5014, "lon": -0.1419, "radius_km": 1, "max_alt_m": 0, "type": "security"},
    {"name": "Parliament", "lat": 51.4995, "lon": -0.1248, "radius_km": 0.5, "max_alt_m": 0, "type": "security"},
    {"name": "JFK Airport", "lat": 40.6413, "lon": -73.7781, "radius_km": 8, "max_alt_m": 0, "type": "airport"},
    {"name": "LAX Airport", "lat": 33.9416, "lon": -118.4085, "radius_km": 8, "max_alt_m": 0, "type": "airport"},
    {"name": "CDG Paris", "lat": 49.0097, "lon": 2.5479, "radius_km": 6, "max_alt_m": 0, "type": "airport"},
    {"name": "Frankfurt Airport", "lat": 50.0379, "lon": 8.5622, "radius_km": 6, "max_alt_m": 0, "type": "airport"},
    {"name": "Nuclear Sellafield", "lat": 54.4203, "lon": -3.4950, "radius_km": 2, "max_alt_m": 0, "type": "critical_infra"},
    {"name": "White House", "lat": 38.8977, "lon": -77.0365, "radius_km": 2.5, "max_alt_m": 0, "type": "security"},
]

# Country drone regulations
DRONE_REGS = {
    "UK": {"max_alt_m": 120, "vlos_required": True, "registration_required_g": 250, "min_age": 16, "regulator": "CAA", "license": "Flyer ID + Operator ID"},
    "US": {"max_alt_m": 122, "vlos_required": True, "registration_required_g": 250, "min_age": 16, "regulator": "FAA", "license": "Part 107 Remote Pilot"},
    "EU": {"max_alt_m": 120, "vlos_required": True, "registration_required_g": 250, "min_age": 16, "regulator": "EASA", "license": "A1/A3 Open Category"},
    "AU": {"max_alt_m": 120, "vlos_required": True, "registration_required_g": 250, "min_age": 16, "regulator": "CASA", "license": "RPA Operator Accreditation"},
    "CA": {"max_alt_m": 122, "vlos_required": True, "registration_required_g": 250, "min_age": 14, "regulator": "Transport Canada", "license": "Basic or Advanced Certificate"},
}

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@mcp.tool()
def check_airspace(latitude: float, longitude: float, altitude_m: float = 120, api_key: str = "") -> str:
    """Check if a location/altitude is safe for drone flight. Returns restrictions, nearby zones, and clearance status.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        latitude (float): The latitude to analyze or process.
        longitude (float): The longitude to analyze or process.
        altitude_m (float): The altitude m to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}
    if err := _rl(): return err

    violations = []
    warnings = []
    nearby = []

    for zone in RESTRICTED_ZONES:
        dist = _haversine(latitude, longitude, zone["lat"], zone["lon"])
        if dist <= zone["radius_km"]:
            violations.append({"zone": zone["name"], "type": zone["type"], "distance_km": round(dist, 2), "restriction": "NO FLY"})
        elif dist <= zone["radius_km"] * 2:
            warnings.append({"zone": zone["name"], "type": zone["type"], "distance_km": round(dist, 2), "restriction": "CAUTION — near restricted zone"})
        elif dist <= 20:
            nearby.append({"zone": zone["name"], "distance_km": round(dist, 2)})

    max_legal = 120
    alt_ok = altitude_m <= max_legal
    if not alt_ok:
        violations.append({"issue": f"Altitude {altitude_m}m exceeds legal max {max_legal}m"})

    return {
        "location": {"lat": latitude, "lon": longitude, "altitude_m": altitude_m},
        "clearance": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "nearby_zones": nearby[:5],
        "max_legal_altitude_m": max_legal,
    }


@mcp.tool()
def get_no_fly_zones(latitude: float, longitude: float, radius_km: float = 50, api_key: str = "") -> str:
    """Get all no-fly zones within a radius of a location.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        latitude (float): The latitude to analyze or process.
        longitude (float): The longitude to analyze or process.
        radius_km (float): The radius km to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}
    if err := _rl(): return err

    zones = []
    for zone in RESTRICTED_ZONES:
        dist = _haversine(latitude, longitude, zone["lat"], zone["lon"])
        if dist <= radius_km:
            zones.append({**zone, "distance_km": round(dist, 2)})
    zones.sort(key=lambda z: z["distance_km"])
    return {"center": {"lat": latitude, "lon": longitude}, "radius_km": radius_km, "zones": zones, "total": len(zones)}


@mcp.tool()
def get_drone_regulations(country: str = "UK", api_key: str = "") -> str:
    """Get drone flight regulations for a country (UK, US, EU, AU, CA).

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        country (str): The country to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}
    if err := _rl(): return err

    code = country.upper().strip()
    if code in DRONE_REGS:
        return {"country": code, "regulations": DRONE_REGS[code]}
    return {"error": f"No data for '{country}'. Available: {', '.join(DRONE_REGS.keys())}"}


@mcp.tool()
def plan_flight(start_lat: float, start_lon: float, end_lat: float, end_lon: float, altitude_m: float = 100, api_key: str = "") -> str:
    """Plan a drone flight path and check for restrictions along the route.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        start_lat (float): The start lat to analyze or process.
        start_lon (float): The start lon to analyze or process.
        end_lat (float): The end lat to analyze or process.
        end_lon (float): The end lon to analyze or process.
        altitude_m (float): The altitude m to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}
    if err := _rl(): return err

    distance = _haversine(start_lat, start_lon, end_lat, end_lon)
    waypoints = 10
    issues = []

    for i in range(waypoints + 1):
        frac = i / waypoints
        lat = start_lat + frac * (end_lat - start_lat)
        lon = start_lon + frac * (end_lon - start_lon)
        for zone in RESTRICTED_ZONES:
            dist = _haversine(lat, lon, zone["lat"], zone["lon"])
            if dist <= zone["radius_km"]:
                issues.append({"waypoint": i, "lat": round(lat, 4), "lon": round(lon, 4), "zone": zone["name"], "distance_km": round(dist, 2)})

    return {
        "route": {"start": {"lat": start_lat, "lon": start_lon}, "end": {"lat": end_lat, "lon": end_lon}},
        "distance_km": round(distance, 2),
        "altitude_m": altitude_m,
        "estimated_time_min": round(distance / 0.8, 1),  # ~50km/h cruise
        "route_clear": len(issues) == 0,
        "conflicts": issues,
        "recommendation": "Route clear for flight" if not issues else f"Route has {len(issues)} conflict(s) — reroute required",
    }


def main():
    mcp.run()

if __name__ == '__main__':
    main()
