import json
import os
import shutil
import tempfile
from threading import RLock
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DEFAULT_CONFIG = BASE_DIR / "data" / "routes-config.default.json"
CONFIG_PATH = Path(os.environ.get("ROUTES_CONFIG_PATH", BASE_DIR / "data" / "routes-config.json"))
UPLOAD_DIR = CONFIG_PATH.parent / "uploads"

app = Flask(__name__, static_folder=None)
config_lock = RLock()


def ensure_config_file():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        shutil.copyfile(DEFAULT_CONFIG, CONFIG_PATH)


def load_config():
    ensure_config_file()
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_config(config):
    ensure_config_file()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=CONFIG_PATH.parent, delete=False) as file:
        json.dump(config, file, ensure_ascii=False, indent=2)
        file.write("\n")
        temporary_name = file.name
    os.replace(temporary_name, CONFIG_PATH)


def upload_subdir(kind):
    folders = {
        "route-asset": "assets-ruta",
        "icon": "iconos",
        "audio": "audios",
        "map": "mapas",
        "decoration": "decoraciones",
    }
    if kind in folders:
        return folders[kind]
    return "misc"


@app.get("/api/config")
def get_config():
    config = load_config()
    referer_path = urlparse(request.referrer or "").path.strip("/")
    route = referer_path.split("/", 1)[0]

    if route in {"1", "2", "3", "4"}:
        config["maps"]["terminal"]["background"] = f"/{route}/assets/images/Nuevo%20fondo%20Barroco.png"

    return jsonify(config)


@app.put("/api/config")
def put_config():
    config = request.get_json(silent=True)
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError:
            config = None

    if not isinstance(config, dict) or "maps" not in config or "catalog" not in config:
        return jsonify({"error": "Configuracion invalida"}), 400

    with config_lock:
        save_config(config)
    return jsonify({"ok": True})


def merge_new_assets(config, catalog, groups):
    """Keep assets saved by other windows; only append newly uploaded assets."""
    for group in groups:
        existing = config["catalog"].setdefault(group, [])
        known = {asset["id"] for asset in existing}
        for asset in catalog.get(group, []):
            if isinstance(asset, dict) and asset.get("id") and asset["id"] not in known:
                existing.append(asset)
                known.add(asset["id"])


@app.patch("/api/maps/<map_key>/routes/<route_id>")
def update_route(map_key, route_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("route"), dict):
        return jsonify({"error": "Ruta invalida"}), 400
    route = payload["route"]
    catalog = payload.get("catalog", {})
    if not isinstance(catalog, dict) or any(not isinstance(catalog.get(key, []), list) for key in ("routeAssets", "audios")):
        return jsonify({"error": "Catalogo invalido"}), 400
    nodes = route.get("nodes")
    if (route.get("id") != route_id or not isinstance(route.get("name"), str)
            or not route["name"].strip() or not isinstance(nodes, list) or len(nodes) < 2
            or any(not isinstance(point, dict) or any(
                type(point.get(axis)) not in (int, float) or not 0 <= point[axis] <= limit
                for axis, limit in (("x", 2000), ("y", 1000))) for point in nodes)):
        return jsonify({"error": "La ruta necesita nombre y al menos dos nodos dentro del mapa"}), 400
    with config_lock:
        config = load_config()
        map_config = config["maps"].get(map_key)
        if map_config is None:
            return jsonify({"error": "Mapa no encontrado"}), 404
        current = next((item for item in map_config["routes"] if item["id"] == route_id), None)
        if current is None:
            return jsonify({"error": "Ruta no encontrada"}), 404
        fields = ("name", "archived", "buttonColor", "instructions", "audio", "assetSize", "nodes", "segmentAssets", "segmentOptions")
        current.update({key: route[key] for key in fields if key in route})
        merge_new_assets(config, catalog, ("routeAssets", "audios"))
        save_config(config)
    return jsonify({"ok": True})


@app.patch("/api/maps/<map_key>")
def update_map(map_key):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("map"), dict):
        return jsonify({"error": "Mapa invalido"}), 400
    catalog = payload.get("catalog", {})
    if not isinstance(catalog, dict) or any(not isinstance(catalog.get(key, []), list) for key in ("backgrounds", "markerIcons", "decorations")):
        return jsonify({"error": "Catalogo invalido"}), 400
    with config_lock:
        config = load_config()
        current = config["maps"].get(map_key)
        if current is None:
            return jsonify({"error": "Mapa no encontrado"}), 404
        fields = ("background", "markers", "decorations")
        current.update({key: payload["map"][key] for key in fields if key in payload["map"]})
        merge_new_assets(config, catalog, ("backgrounds", "markerIcons", "decorations"))
        save_config(config)
    return jsonify({"ok": True})


@app.get("/dashboard")
@app.get("/dashboard/")
def dashboard():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


@app.post("/api/upload")
def upload_file():
    uploaded_file = request.files.get("file")
    kind = upload_subdir(request.form.get("kind", "misc"))

    if uploaded_file is None or uploaded_file.filename == "":
      return jsonify({"error": "Archivo requerido"}), 400

    target_dir = UPLOAD_DIR / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    original_name = secure_filename(uploaded_file.filename)
    suffix = Path(original_name).suffix.lower()
    filename = f"{uuid4().hex}{suffix}"
    uploaded_file.save(target_dir / filename)

    return jsonify({
        "src": f"/uploads/{kind}/{filename}",
        "name": Path(original_name).stem or "Archivo"
    })


@app.get("/")
def terminal():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/Conf")
@app.get("/Conf/")
def terminal_config():
    return send_from_directory(FRONTEND_DIR, "conf.html")


@app.get("/MapaR")
@app.get("/MapaR/")
def mapar():
    return send_from_directory(FRONTEND_DIR / "MapaR", "index.html")


@app.get("/MapaR/Conf")
@app.get("/MapaR/Conf/")
def mapar_config():
    return send_from_directory(FRONTEND_DIR, "conf.html")


THEME_FOLDERS = {
    "1": "Anteriores/Clasmorfismo",
    "2": "Anteriores/Glaymorfismo",
    "3": "Anteriores/Minimalismo",
    "4": "Anteriores/LiquidGlass",
    "11": "Clasmorfismo",
    "22": "Glaymorfismo",
    "33": "Minimalismo",
    "44": "LiquidGlass",
}


@app.get("/fork-core/<path:path>")
def fork_core_files(path):
    return send_from_directory(BASE_DIR / "fork-core", path)


@app.get("/<theme>/<path:path>")
def theme_files(theme, path):
    folder = THEME_FOLDERS.get(theme)
    if folder is None:
        return static_files(f"{theme}/{path}")
    return send_from_directory(BASE_DIR / folder, path)


@app.get("/<theme>")
@app.get("/<theme>/")
def theme_preview(theme):
    folder = THEME_FOLDERS.get(theme)
    if folder is None:
        return static_files(theme)
    return send_from_directory(BASE_DIR / folder, "index.html")


@app.get("/uploads/<path:path>")
def uploaded_files(path):
    return send_from_directory(UPLOAD_DIR, path)


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "80")))
