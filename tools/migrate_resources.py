"""Migrate resource catalogs and files. Dry run by default; --apply writes backups."""
import argparse
import copy
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.resources import GROUPS, SHARED, ResourceLibrary, resource_url, rewrite_urls, section_folder
from backend.storage import ConfigStore


def owner_for(asset, group, config):
    if group == "backgrounds" or asset.get("id") == "muni-logo":
        return SHARED
    if asset.get("sectionId"):
        return asset["sectionId"]
    values = [asset.get("src", ""), *asset.get("directions", {}).values()]
    if any(value.startswith("/MapaR/") for value in values):
        return "mapar"
    if any(value.startswith("/assets/") for value in values):
        return "terminal"
    for key, map_config in config["maps"].items():
        if group == "routeAssets" and any(asset["id"] in route.get("segmentAssets", []) for route in map_config["routes"]):
            return key
        if group == "audios" and any(asset.get("src") == route.get("audio") for route in map_config["routes"]):
            return key
        field = {"markerIcons": "markers", "decorations": "decorations"}.get(group)
        if field and any(item.get("assetId") == asset["id"] for item in map_config.get(field, [])):
            return key
    return SHARED


def migrate(project_root, apply=False):
    project_root = Path(project_root).resolve()
    data = project_root / "data"
    paths = [data / "routes-config.json", data / "routes-config.default.json"]
    documents = {path: json.loads(path.read_text(encoding="utf-8")) for path in paths}
    aliases_path = data / "resource-aliases.json"
    aliases = json.loads(aliases_path.read_text(encoding="utf-8")) if aliases_path.exists() else {}
    copies = {}
    migrated = {}
    store = ConfigStore(lambda: paths[0], lambda: paths[1])
    library = ResourceLibrary(store)

    def relocate(url, group, owner):
        if not url or not url.startswith("/") or url.startswith("/recursos/"):
            return url
        decoded = unquote(urlsplit(url).path)
        if decoded in aliases:
            return aliases[decoded]
        if decoded.startswith("/uploads/"):
            source = data / decoded.lstrip("/")
        else:
            source = project_root / "frontend" / decoded.lstrip("/")
        source = source.resolve()
        if not source.is_relative_to(project_root) or not source.is_file():
            raise ValueError(f"Recurso no encontrado: {url}")
        relative = library.relative_folder(group, owner) / source.name
        target = (library.root / relative).resolve()
        if target in copies and copies[target].read_bytes() != source.read_bytes():
            relative = relative.with_name(hashlib.sha256(decoded.encode()).hexdigest()[:10] + "-" + source.name)
            target = (library.root / relative).resolve()
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError(f"Conflicto de archivos: {target}")
        copies[target] = source
        aliases[decoded] = resource_url(relative)
        return aliases[decoded]

    for path, original in documents.items():
        config = copy.deepcopy(original)
        for group in GROUPS:
            for asset in config["catalog"].get(group, []):
                owner = owner_for(asset, group, config)
                asset["sectionId"] = owner
                if asset.get("src"):
                    asset["src"] = relocate(asset["src"], group, owner)
                if asset.get("directions"):
                    asset["directions"] = {direction: relocate(url, group, owner) for direction, url in asset["directions"].items()}
        for key, map_config in config["maps"].items():
            map_config["resourceFolder"] = section_folder(key)
            map_config["background"] = relocate(map_config["background"], "backgrounds", SHARED)
            map_config["logo"] = relocate(map_config["logo"], "markerIcons", SHARED)
            for route in map_config["routes"]:
                if route.get("audio"):
                    route["audio"] = relocate(route["audio"], "audios", key)
        config["resourceSchemaVersion"] = 1
        migrated[path] = config

    # A URL can occur in another document before its catalog entry is visited.
    migrated = {path: rewrite_urls(config, aliases) for path, config in migrated.items()}
    changed = [path for path in paths if migrated[path] != documents[path]]
    if not apply:
        return {"files": len(copies), "configs": len(changed), "applied": False}
    backup = None
    if changed:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = data / "backups" / ("recursos-" + stamp)
        backup.mkdir(parents=True)
        for path in paths:
            shutil.copy2(path, backup / path.name)
        if aliases_path.exists():
            shutil.copy2(aliases_path, backup / aliases_path.name)
    for target, source in copies.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
            raise ValueError(f"La copia no coincide: {target}")
    for config in migrated.values():
        library.ensure_layout(config)
    written = []
    try:
        ConfigStore(lambda: aliases_path, lambda: paths[1]).save(aliases)
        for path in changed:
            ConfigStore(lambda path=path: path, lambda: paths[1]).save(migrated[path])
            written.append(path)
    except Exception:
        for path in written:
            ConfigStore(lambda path=path: path, lambda: paths[1]).save(documents[path])
        raise
    return {"files": len(copies), "configs": len(changed), "applied": True, "backup": str(backup) if backup else None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(ROOT, args.apply), ensure_ascii=False, indent=2))
