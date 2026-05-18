import math
from Updater import haversine


def point_to_segment_distance(px: float, py: float,
                               ax: float, ay: float,
                               bx: float, by: float) -> float:
    """Calculate the minimum distance from point P to line segment AB.
    All coordinates are in degrees (lat/lon).
    Returns distance in km.
    """
    # Vector AB
    abx = bx - ax
    aby = by - ay

    # If segment is a point
    if abx == 0 and aby == 0:
        return haversine(px, py, ax, ay)

    # Project point P onto line AB, compute parameter t
    t = ((px - ax) * abx + (py - ay) * aby) / (abx ** 2 + aby ** 2)

    # Clamp t to [0, 1] to stay within segment
    t = max(0.0, min(1.0, t))

    # Closest point on segment to P
    closest_x = ax + t * abx
    closest_y = ay + t * aby

    return haversine(px, py, closest_x, closest_y)


def check_path_conflicts(user_lat: float, user_lon: float,
                          resource_lat: float, resource_lon: float,
                          events: list,
                          threshold_km: float = 0.5) -> list:
    """Check if any conflict events fall within threshold_km of the path
    from user to resource. Returns list of conflicting events."""
    conflicts_on_path = []

    for event in events:
        dist = point_to_segment_distance(
            event["latitude"], event["longitude"],
            user_lat, user_lon,
            resource_lat, resource_lon
        )
        if dist <= threshold_km:
            conflicts_on_path.append({
                **event,
                "path_distance_km": round(dist, 2),
            })

    return conflicts_on_path


def build_path_conflict_context(resource: dict, conflicts: list) -> str:
    """Build a context string describing path conflicts for a resource."""
    if not conflicts:
        return ""

    lines = [
        f"⚠️ PATH WARNING: Route to '{resource['name']}' ({resource['type']}) "
        f"passes through {len(conflicts)} conflict zone(s):"
    ]
    for c in conflicts:
        lines.append(
            f"  - [{c['severity'].upper()}] {c['event_type']} in {c['region']} "
            f"({c['path_distance_km']} km from your route): {c['description']}"
        )
    return "\n".join(lines)


def get_path_conflict_context(user_lat: float, user_lon: float,
                               resources: list, events: list,
                               threshold_km: float = 0.5) -> str:
    """For each resource, check path conflicts and build full context string."""
    all_warnings = []

    for resource in resources:
        conflicts = check_path_conflicts(
            user_lat, user_lon,
            resource["latitude"], resource["longitude"],
            events,
            threshold_km=threshold_km
        )
        warning = build_path_conflict_context(resource, conflicts)
        if warning:
            all_warnings.append(warning)

    return "\n\n".join(all_warnings)