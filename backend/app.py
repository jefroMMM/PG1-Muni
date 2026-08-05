import json
import os
import shutil
import tempfile
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

    save_config(config)
    return jsonify({"ok": True})


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
