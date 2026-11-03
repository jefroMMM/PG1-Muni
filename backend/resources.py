"""Section-owned resource folders and compatibility with migrated URLs."""
import copy
import json
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

GROUPS = {"routeAssets": "assets", "audios": "audios", "markerIcons": "iconos", "decorations": "decoraciones", "backgrounds": "Fondos"}
KINDS = {"route-asset": "routeAssets", "audio": "audios", "icon": "markerIcons", "decoration": "decorations", "map": "backgrounds"}
SHARED = "shared"


def section_folder(key):
    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", key):
        raise ValueError("Identificador de sección inválido")
    return {"terminal": "Mapa", "mapar": "MapaR", SHARED: "Compartidos"}.get(key, key)


def resource_url(relative):
    return "/recursos/" + quote(Path(relative).as_posix(), safe="/")


def rewrite_urls(value, aliases):
    if isinstance(value, str):
        return aliases.get(unquote(value), value)
    if isinstance(value, list):
        return [rewrite_urls(item, aliases) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_urls(item, aliases) for key, item in value.items()}
    return value


class ResourceLibrary:
    def __init__(self, store):
        self.store = store
        self._json_cache = {}

    def _read_json(self, path):
        info = path.stat()
        stamp = (str(path.resolve()), info.st_mtime_ns, info.st_size, info.st_ino)
        cached = self._json_cache.get(str(path))
        if cached is None or cached[0] != stamp:
            cached = (stamp, json.loads(path.read_text(encoding="utf-8")))
            self._json_cache[str(path)] = cached
        return cached[1]

    @property
    def root(self):
        return self.store.get_path().parent / "recursos"

    def relative_folder(self, group, section_id):
        category = GROUPS[group]
        return Path(category) if group == "backgrounds" else Path(category) / section_folder(section_id)

    def ensure_section(self, key):
        for group in GROUPS:
            directory = self.root / self.relative_folder(group, key)
            directory.mkdir(parents=True, exist_ok=True)
            if not (directory / ".gitkeep").exists():
                (directory / ".gitkeep").touch()

    def ensure_layout(self, config):
        self.ensure_section(SHARED)
        for key in config["maps"]:
            self.ensure_section(key)

    def aliases(self):
        path = self.store.get_path().parent / "resource-aliases.json"
        if not path.exists():
            path = self.store.get_default_path().parent / "resource-aliases.json"
        return self._read_json(path) if path.exists() else {}

    def canonicalize(self, payload):
        return rewrite_urls(payload, self.aliases())

    def resolve(self, relative):
        parts = relative.split("/")
        if not parts or parts[0] not in GROUPS.values() or any(not part or part.startswith(".") or "\\" in part for part in parts):
            return None
        candidate = self.root.joinpath(*parts).resolve()
        if not candidate.is_relative_to(self.root.resolve()):
            return None
        if candidate.is_file():
            return candidate
        # Isolated test/development stores can read bundled seed media without
        # writing to the real library or sharing newly uploaded test files.
        default_path = self.store.get_default_path()
        default = self._read_json(default_path)
        known = set()

        def collect(value):
            if isinstance(value, str):
                known.add(unquote(value))
            elif isinstance(value, dict):
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)

        collect(default)
        fallback = default_path.parent / "recursos" / Path(*parts)
        return fallback if "/recursos/" + relative in known and fallback.is_file() else None

    def merge_catalog(self, incoming, current):
        """Preserve server-owned upload metadata and uploads from other tabs."""
        result = copy.deepcopy(incoming)
        for group in GROUPS:
            existing = {asset["id"]: asset for asset in current.get(group, [])}
            supplied = result.setdefault(group, [])
            supplied_ids = {asset["id"] for asset in supplied}
            for asset in supplied:
                if asset["id"] in existing:
                    original = existing[asset["id"]]
                    for field in ("src", "directions", "sectionId"):
                        if field in original:
                            asset[field] = copy.deepcopy(original[field])
            supplied.extend(copy.deepcopy(asset) for key, asset in existing.items() if key not in supplied_ids)
        return result
