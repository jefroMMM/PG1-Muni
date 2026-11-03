"""Shared route validation and catalog merging."""
from .resources import section_folder
ROUTE_FIELDS = ("name", "archived", "buttonColor", "instructions", "instructionSteps",
                "durationSeconds", "highlightPolygon", "audio", "assetSize", "nodes",
                "segmentAssets", "segmentOptions")


def merge_new_assets(config, catalog, groups):
    """Keep assets saved by other windows; only append newly uploaded assets."""
    for group in groups:
        existing = config["catalog"].setdefault(group, [])
        known = {asset["id"] for asset in existing}
        for asset in catalog.get(group, []):
            if isinstance(asset, dict) and asset.get("id") and asset["id"] not in known:
                existing.append(asset)
                known.add(asset["id"])


def valid_highlight(value):
    if value == "":
        return True
    if not isinstance(value, str):
        return False
    try:
        points = [tuple(float(axis) for axis in pair.split(",")) for pair in value.split()]
        if len(points) != 4 or any(len(point) != 2 or not (0 <= point[0] <= 2000 and 0 <= point[1] <= 1000) for point in points):
            return False
        turns = []
        for index, (x, y) in enumerate(points):
            nx, ny = points[(index + 1) % 4]
            ex, ey = points[(index + 2) % 4]
            turns.append((nx - x) * (ey - ny) - (ny - y) * (ex - nx))
        return all(turn > 0 for turn in turns) or all(turn < 0 for turn in turns)
    except (ValueError, TypeError):
        return False


def valid_route(route, route_id):
    if not isinstance(route, dict):
        return False
    nodes = route.get("nodes")
    return (route.get("id") == route_id and isinstance(route_id, str) and bool(route_id)
            and ("highlightPolygon" not in route or valid_highlight(route["highlightPolygon"]))
            and ("durationSeconds" not in route or (
                type(route["durationSeconds"]) in (int, float)
                and 3 <= route["durationSeconds"] <= 3600))
            and isinstance(route.get("name"), str) and bool(route["name"].strip())
            and ("instructionSteps" not in route or (
                isinstance(route["instructionSteps"], list)
                and all(isinstance(step, str) for step in route["instructionSteps"])))
            and isinstance(nodes, list) and len(nodes) >= 2
            and all(isinstance(point, dict) and all(
                type(point.get(axis)) in (int, float) and 0 <= point[axis] <= limit
                for axis, limit in (("x", 2000), ("y", 1000))) for point in nodes))


def valid_catalog(catalog, groups):
    if not isinstance(catalog, dict):
        return False
    for group in groups:
        assets = catalog.get(group, [])
        if not isinstance(assets, list) or any(
            not isinstance(asset, dict) or not isinstance(asset.get("id"), str) or not asset["id"]
            for asset in assets
        ):
            return False
        if any("sectionId" in asset and (not isinstance(asset["sectionId"], str) or not asset["sectionId"]) for asset in assets):
            return False
    return True


def valid_map_fields(value):
    return (isinstance(value, dict)
            and ("background" not in value or isinstance(value["background"], str))
            and all(key not in value or (isinstance(value[key], list) and all(isinstance(item, dict) for item in value[key]))
                    for key in ("markers", "decorations")))


def valid_config(config):
    if not isinstance(config, dict) or not isinstance(config.get("maps"), dict):
        return False
    if not {"terminal", "mapar"}.issubset(config["maps"]):
        return False
    if not valid_catalog(config.get("catalog"), ("routeAssets", "audios", "backgrounds", "markerIcons", "decorations")):
        return False
    for key, value in config["maps"].items():
        try:
            section_folder(key)
        except ValueError:
            return False
        if not valid_map_fields(value) or not isinstance(value.get("routes"), list):
            return False
        ids = set()
        for route in value["routes"]:
            if not isinstance(route, dict) or not valid_route(route, route.get("id")) or route["id"] in ids:
                return False
            ids.add(route["id"])
    return True
