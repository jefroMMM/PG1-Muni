"""Fixtures simplificadas de tests/bdd/conftest.py: copia temporal y servidor propio."""
import hashlib
import importlib
import json
import os
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server


def project_root():
    configured = os.environ.get("BDD_PROJECT_ROOT")
    candidates = [Path(configured).resolve()] if configured else Path(__file__).resolve().parents
    for path in candidates:
        if ((path / "backend/app.py").is_file()
                and (path / "data/routes-config.default.json").is_file()
                and (path / "frontend/conf.html").is_file()):
            return path
    raise pytest.UsageError("Define BDD_PROJECT_ROOT con la carpeta del proyecto PG1-Muni.")


ROOT = project_root()
sys.path.insert(0, str(ROOT))
backend = importlib.import_module("backend.app")


@pytest.fixture(scope="session", autouse=True)
def protected_files():
    """Verifica integridad sin escribir en los datos originales ni en las cargas."""
    paths = [ROOT / "data/routes-config.json", ROOT / "data/routes-config.default.json"]

    def snapshot():
        files = paths + list((ROOT / "data/uploads").rglob("*"))
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
                for p in files if not p.is_dir()}

    before = snapshot()
    yield
    assert snapshot() == before, "Los datos originales o los archivos cargados cambiaron"


@pytest.fixture
def ctx(tmp_path, monkeypatch, protected_files):
    # Mismo aislamiento del laboratorio existente, restaurado por monkeypatch.
    config_path = tmp_path / "data/routes-config.json"
    monkeypatch.setattr(backend, "CONFIG_PATH", config_path)
    monkeypatch.setattr(backend, "UPLOAD_DIR", config_path.parent / "uploads")
    monkeypatch.setitem(backend.app.config, "TESTING", True)
    seed = json.loads(backend.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    backend.save_config(seed)
    state = SimpleNamespace(initial=seed, config_path=config_path,
                            route_id=seed["maps"]["terminal"]["routes"][0]["id"])
    state.read = lambda: json.loads(config_path.read_text(encoding="utf-8"))
    yield state


@pytest.fixture
def live_server(ctx):
    server = make_server("127.0.0.1", 0, backend.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    ctx.base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(ctx.base_url + "/api/config", timeout=3) as response:
            assert response.status == 200
            assert json.load(response) == ctx.initial
        yield ctx.base_url
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        assert not thread.is_alive(), "El servidor temporal no terminó"


@pytest.fixture
def browser(ctx, live_server):
    # ChromeDriver crea un perfil temporal por escenario, como en tests/bdd.
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    if os.environ.get("BDD_CHROME_BINARY"):
        options.binary_location = os.environ["BDD_CHROME_BINARY"]
    service = (Service(executable_path=os.environ["BDD_CHROMEDRIVER"])
               if os.environ.get("BDD_CHROMEDRIVER") else Service())
    driver = webdriver.Chrome(service=service, options=options)
    ctx.driver = driver
    try:
        driver.set_page_load_timeout(30)
        WebDriverWait(driver, 15).until(
            lambda d: d.current_url == "data:,"
            and d.execute_script("return document.readyState") == "complete")
        yield driver
    finally:
        driver.quit()
