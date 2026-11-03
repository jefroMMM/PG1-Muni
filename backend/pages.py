"""HTML pages and public file delivery; archived sources are never served."""
from flask import Blueprint, abort, jsonify, redirect, send_from_directory
from urllib.parse import unquote


def create_pages(store, frontend_dir, get_upload_dir, resources):
    pages = Blueprint("pages", __name__)

    @pages.get("/dashboard")
    @pages.get("/dashboard/")
    def dashboard():
        return send_from_directory(frontend_dir, "dashboard.html")


    @pages.get("/dashboard2")
    @pages.get("/dashboard2/")
    def dashboard_professional():
        return send_from_directory(frontend_dir, "dashboard2.html")


    @pages.get("/preview")
    def route_preview():
        return send_from_directory(frontend_dir, "preview.html")


    @pages.get("/maps/<map_key>")
    @pages.get("/maps/<map_key>/")
    def section_viewer(map_key):
        if map_key in {"terminal", "mapar"}:
            abort(404)
        if map_key not in store.load()["maps"]:
            return jsonify({"error": "Sección no encontrada"}), 404
        return send_from_directory(frontend_dir, "index.html")


    @pages.get("/maps/<map_key>/Conf")
    def section_editor(map_key):
        if map_key in {"terminal", "mapar"}:
            abort(404)
        if map_key not in store.load()["maps"]:
            return jsonify({"error": "Sección no encontrada"}), 404
        return send_from_directory(frontend_dir, "conf.html")


    @pages.get("/")
    def terminal():
        return send_from_directory(frontend_dir, "index.html")


    @pages.get("/Conf")
    @pages.get("/Conf/")
    def terminal_config():
        return send_from_directory(frontend_dir, "conf.html")


    @pages.get("/MapaR")
    @pages.get("/MapaR/")
    def mapar():
        return send_from_directory(frontend_dir / "MapaR", "index.html")


    @pages.get("/MapaR/Conf")
    @pages.get("/MapaR/Conf/")
    def mapar_config():
        return send_from_directory(frontend_dir, "conf.html")


    @pages.get("/uploads/<path:path>")
    def uploaded_files(path):
        alias = resources.aliases().get("/uploads/" + unquote(path))
        if alias:
            return redirect(alias, code=302)
        return send_from_directory(get_upload_dir(), path)

    @pages.get("/recursos/<path:path>")
    def resource_files(path):
        target = resources.resolve(path)
        if target is None:
            abort(404)
        return send_from_directory(target.parent, target.name)

    @pages.get("/<path:path>")
    def static_files(path):
        alias = resources.aliases().get("/" + unquote(path))
        if alias:
            return redirect(alias, code=302)
        return send_from_directory(frontend_dir, path)

    return pages
