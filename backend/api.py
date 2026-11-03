"""JSON endpoints for configuration, sections, routes and uploads."""
import copy
import json
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from .validation import ROUTE_FIELDS, merge_new_assets, valid_route, valid_catalog, valid_config, valid_map_fields
from .resources import KINDS, SHARED, resource_url, section_folder


def create_api(store, resources):
    api = Blueprint("api", __name__)

    @api.get("/api/config")
    def get_config():
        config = store.load()
        resources.ensure_layout(config)
        return jsonify(config)


    @api.put("/api/config")
    def put_config():
        config = request.get_json(silent=True)
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = None

        if not valid_config(config):
            return jsonify({"error": "Configuracion invalida"}), 400

        with store.lock:
            config = resources.canonicalize(config)
            config["catalog"] = resources.merge_catalog(config["catalog"], store.load()["catalog"])
            config["resourceSchemaVersion"] = 1
            for key, map_config in config["maps"].items():
                map_config["resourceFolder"] = section_folder(key)
            resources.ensure_layout(config)
            store.save(config)
        return jsonify({"ok": True})


    @api.post("/api/maps")
    def create_map():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("name"), str) or not payload["name"].strip() or len(payload["name"].strip()) > 80:
            return jsonify({"error": "Escribe un nombre de sección de hasta 80 caracteres"}), 400
        icon = payload.get("icon", "building")
        template = payload.get("template", "terminal")
        if not isinstance(icon, str) or not isinstance(template, str) or icon not in {"building", "map", "pin", "briefcase", "health", "school", "bus", "park"} or template not in {"terminal", "mapar"}:
            return jsonify({"error": "Selecciona un icono y un mapa inicial válidos"}), 400
        with store.lock:
            config = store.load()
            key = f"seccion-{uuid4().hex[:12]}"
            new_map = copy.deepcopy(config["maps"][template])
            name = payload["name"].strip()
            new_map.update({"sectionName": name, "sectionIcon": icon, "title": name, "routes": [], "markers": [], "decorations": []})
            new_map["resourceFolder"] = section_folder(key)
            new_map["defaultPanel"] = {"title": name, "kicker": "Municipalidad de Retalhuleu", "text": "Selecciona una ruta para consultar el recorrido.", "hint": ""}
            config["maps"][key] = new_map
            resources.ensure_section(key)
            store.save(config)
        return jsonify({"ok": True, "mapKey": key}), 201


    @api.post("/api/maps/<map_key>/routes")
    def create_route(map_key):
        payload = resources.canonicalize(request.get_json(silent=True))
        route = payload.get("route") if isinstance(payload, dict) else None
        if not isinstance(route, dict) or not valid_route(route, route.get("id")):
            return jsonify({"error": "La ruta necesita nombre y al menos dos nodos dentro del mapa"}), 400
        catalog = payload.get("catalog", {})
        if not valid_catalog(catalog, ("routeAssets", "audios")):
            return jsonify({"error": "Catalogo invalido"}), 400
        with store.lock:
            config = store.load()
            map_config = config["maps"].get(map_key)
            if map_config is None:
                return jsonify({"error": "Mapa no encontrado"}), 404
            if any(item["id"] == route["id"] for item in map_config["routes"]):
                return jsonify({"error": "Esta ruta ya existe"}), 409
            fields = ("id", *ROUTE_FIELDS)
            map_config["routes"].append({key: route[key] for key in fields if key in route})
            merge_new_assets(config, catalog, ("routeAssets", "audios"))
            store.save(config)
        return jsonify({"ok": True}), 201


    @api.patch("/api/maps/<map_key>/routes/<route_id>")
    def update_route(map_key, route_id):
        payload = resources.canonicalize(request.get_json(silent=True))
        if not isinstance(payload, dict) or not isinstance(payload.get("route"), dict):
            return jsonify({"error": "Ruta invalida"}), 400
        route = payload["route"]
        catalog = payload.get("catalog", {})
        if not valid_catalog(catalog, ("routeAssets", "audios")):
            return jsonify({"error": "Catalogo invalido"}), 400
        if not valid_route(route, route_id):
            return jsonify({"error": "La ruta necesita nombre y al menos dos nodos dentro del mapa"}), 400
        with store.lock:
            config = store.load()
            map_config = config["maps"].get(map_key)
            if map_config is None:
                return jsonify({"error": "Mapa no encontrado"}), 404
            current = next((item for item in map_config["routes"] if item["id"] == route_id), None)
            if current is None:
                return jsonify({"error": "Ruta no encontrada"}), 404
            fields = ROUTE_FIELDS
            current.update({key: route[key] for key in fields if key in route})
            merge_new_assets(config, catalog, ("routeAssets", "audios"))
            store.save(config)
        return jsonify({"ok": True})


    @api.patch("/api/maps/<map_key>/routes/<route_id>/status")
    def set_route_status(map_key, route_id):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get("archived")) is not bool:
            return jsonify({"error": "Estado de ruta inválido"}), 400
        with store.lock:
            config = store.load()
            map_config = config["maps"].get(map_key)
            if map_config is None:
                return jsonify({"error": "Mapa no encontrado"}), 404
            route = next((route for route in map_config["routes"] if route["id"] == route_id), None)
            if route is None:
                return jsonify({"error": "Ruta no encontrada"}), 404
            route["archived"] = payload["archived"]
            store.save(config)
        return jsonify({"ok": True})

    @api.delete("/api/maps/<map_key>/routes/<route_id>")
    def delete_route(map_key, route_id):
        with store.lock:
            config = store.load()
            map_config = config["maps"].get(map_key)
            if map_config is None:
                return jsonify({"error": "Mapa no encontrado"}), 404
            remaining = [route for route in map_config["routes"] if route["id"] != route_id]
            if len(remaining) == len(map_config["routes"]):
                return jsonify({"error": "Ruta no encontrada"}), 404
            map_config["routes"] = remaining
            store.save(config)
        return jsonify({"ok": True})

    @api.patch("/api/maps/<map_key>")
    def update_map(map_key):
        payload = resources.canonicalize(request.get_json(silent=True))
        if not isinstance(payload, dict) or not valid_map_fields(payload.get("map")):
            return jsonify({"error": "Mapa invalido"}), 400
        catalog = payload.get("catalog", {})
        if not valid_catalog(catalog, ("backgrounds", "markerIcons", "decorations")):
            return jsonify({"error": "Catalogo invalido"}), 400
        with store.lock:
            config = store.load()
            current = config["maps"].get(map_key)
            if current is None:
                return jsonify({"error": "Mapa no encontrado"}), 404
            fields = ("background", "markers", "decorations")
            current.update({key: payload["map"][key] for key in fields if key in payload["map"]})
            merge_new_assets(config, catalog, ("backgrounds", "markerIcons", "decorations"))
            store.save(config)
        return jsonify({"ok": True})


    @api.post("/api/upload")
    def upload_file():
        uploaded_file = request.files.get("file")
        if uploaded_file is None or uploaded_file.filename == "":
            return jsonify({"error": "Archivo requerido"}), 400
        kind = request.form.get("kind")
        map_key = request.form.get("mapKey")
        if kind not in KINDS:
            return jsonify({"error": "Tipo de recurso inválido"}), 400
        original_name = secure_filename(uploaded_file.filename)
        if not original_name:
            return jsonify({"error": "Nombre de archivo inválido"}), 400
        suffix = Path(original_name).suffix.lower()
        allowed = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".webm", ".flac"} if kind == "audio" else {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}
        if suffix not in allowed:
            return jsonify({"error": "Formato de archivo no admitido para este recurso"}), 400
        filename = f"{uuid4().hex}{suffix}"
        with store.lock:
            config = store.load()
            if map_key not in config["maps"]:
                return jsonify({"error": "Selecciona una sección válida"}), 400
            group = KINDS[kind]
            owner = SHARED if kind == "map" else map_key
            relative = resources.relative_folder(group, owner) / filename
            target = resources.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            asset = {"id": f"{kind}-{uuid4().hex}", "src": resource_url(relative),
                     "name": Path(original_name).stem, "sectionId": owner}
            if kind == "route-asset":
                asset["type"] = "single"
            try:
                uploaded_file.save(target)
                config["catalog"].setdefault(group, []).append(asset)
                store.save(config)
            except Exception:
                target.unlink(missing_ok=True)
                raise
        return jsonify(asset), 201

    return api
