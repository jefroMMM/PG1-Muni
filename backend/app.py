"""Application entry point. Run with: python -m backend.app."""
import os
from pathlib import Path

from flask import Flask

from .api import create_api
from .pages import create_pages
from .storage import ConfigStore
from .resources import ResourceLibrary


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DEFAULT_CONFIG = BASE_DIR / "data" / "routes-config.default.json"
CONFIG_PATH = Path(os.environ.get("ROUTES_CONFIG_PATH", BASE_DIR / "data" / "routes-config.json"))
UPLOAD_DIR = CONFIG_PATH.parent / "uploads"

store = ConfigStore(lambda: CONFIG_PATH, lambda: DEFAULT_CONFIG)

# Retain these helpers for scripts and isolated test fixtures.
load_config = store.load
save_config = store.save
ensure_config_file = store.ensure_file


def create_app(config_store=None, upload_dir=None):
    application = Flask(__name__, static_folder=None)
    repository = config_store or store
    get_upload_dir = (lambda: Path(upload_dir)) if upload_dir is not None else (lambda: UPLOAD_DIR)
    resources = ResourceLibrary(repository)
    application.register_blueprint(create_api(repository, resources))
    application.register_blueprint(create_pages(repository, FRONTEND_DIR, get_upload_dir, resources))
    return application


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "80")))
