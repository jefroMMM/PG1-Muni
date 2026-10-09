"""Fixtures aisladas, navegador y reportes; no inicia el servidor de producción."""
import hashlib
import importlib.metadata
import json
import os
import platform
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from werkzeug.serving import make_server

from backend import app as backend

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).parent / "reports"
RESULTS = {}
ENVIRONMENT = {}
SCENARIO_NAMES = {}


def pytest_bdd_before_scenario(request, feature, scenario):
    SCENARIO_NAMES[request.node.nodeid] = scenario.name


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    state = step_func_args.get("ctx")
    if state is not None and hasattr(state, "driver"):
        REPORTS.mkdir(exist_ok=True)
        scenario_id = next((m.name for m in request.node.iter_markers() if m.name.startswith("BDD")), "unknown")
        try:
            state.driver.save_screenshot(str(REPORTS / f"{scenario_id}-failure.png"))
        except Exception:
            pass  # El error original sigue registrado si la captura no es posible.


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def protected_files():
    paths = [ROOT / "data/routes-config.json", ROOT / "data/routes-config.default.json",
             ROOT / "frontend/assets/css/styles.css",
             Path(__file__).parent / "features/edicion_rutas_administrativas.feature"]
    paths += list((ROOT / "data/uploads").rglob("*"))
    before = {str(p): digest(p) for p in paths if p.is_file()}
    ENVIRONMENT["protected_sha256_before"] = before
    yield
    after = {str(p): digest(p) if p.is_file() else None for p in paths if str(p) in before}
    new_uploads = {str(p) for p in (ROOT / "data/uploads").rglob("*") if p.is_file()} - set(before)
    ENVIRONMENT["protected_sha256_after"] = after
    ENVIRONMENT["real_data_unchanged"] = before == after and not new_uploads
    assert before == after and not new_uploads, "Cambió un archivo protegido o se creó una carga real"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    config_path = tmp_path / "data" / "routes-config.json"
    uploads = tmp_path / "data" / "uploads"
    monkeypatch.setattr(backend, "CONFIG_PATH", config_path)
    monkeypatch.setattr(backend, "UPLOAD_DIR", uploads)
    monkeypatch.setitem(backend.app.config, "TESTING", True)
    seed = json.loads(backend.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    backend.save_config(seed)
    state = SimpleNamespace(initial=seed, route_id=seed["maps"]["terminal"]["routes"][0]["id"],
                            map_key="terminal", client=backend.app.test_client(), web_responses=[],
                            expected={}, config_path=config_path, results=[])
    state.read = lambda: json.loads(config_path.read_text(encoding="utf-8"))
    state.route = lambda: next(r for r in state.read()["maps"][state.map_key]["routes"]
                              if r["id"] == state.route_id)
    original_wsgi = backend.app.wsgi_app

    def observe_wsgi(environ, start_response):
        def observed_response(status, headers, exc_info=None):
            if environ["REQUEST_METHOD"] == "PATCH":
                state.web_responses.append({"path": environ["PATH_INFO"], "status": int(status.split()[0])})
            return start_response(status, headers, exc_info)
        return original_wsgi(environ, observed_response)

    monkeypatch.setattr(backend.app, "wsgi_app", observe_wsgi)
    yield state


@pytest.fixture
def live_server(ctx):
    server = make_server("127.0.0.1", 0, backend.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    assert not thread.is_alive(), "El servidor temporal no terminó"


@pytest.fixture
def browser(ctx, live_server, tmp_path):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument(f"--user-data-dir={tmp_path / 'chrome-profile'}")
    options.set_capability("unhandledPromptBehavior", "accept")
    if os.environ.get("BDD_CHROME_BINARY"):
        options.binary_location = os.environ["BDD_CHROME_BINARY"]
    service = Service(executable_path=os.environ["BDD_CHROMEDRIVER"]) if os.environ.get("BDD_CHROMEDRIVER") else Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    ENVIRONMENT["browser"] = driver.capabilities.get("browserName")
    ENVIRONMENT["browser_version"] = driver.capabilities.get("browserVersion")
    ctx.driver, ctx.base_url = driver, live_server
    yield driver
    driver.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    if "piloto" not in item.keywords:
        return
    entry = RESULTS.setdefault(item.nodeid, {"id": next((m.name for m in item.iter_markers()
                                                       if m.name.startswith("BDD")), ""),
                                           "test": item.name, "scenario": SCENARIO_NAMES.get(item.nodeid, item.name),
                                           "phases": [], "duration": 0})
    entry["duration"] += report.duration
    entry["phases"].append({"phase": report.when, "outcome": report.outcome,
                             "cause": str(report.longrepr) if report.failed or report.skipped else ""})
    if report.failed and "browser" in item.funcargs:
        REPORTS.mkdir(exist_ok=True)
        try:
            item.funcargs["browser"].save_screenshot(str(REPORTS / f"{entry['id']}-failure.png"))
        except Exception:
            pass  # El reporte original se conserva aunque el navegador ya no exista.


def pytest_sessionfinish(session, exitstatus):
    REPORTS.mkdir(exist_ok=True)
    # Guatemala utiliza UTC-6 sin cambio estacional; funciona también sin tzdata en Windows.
    timestamp = datetime.now(timezone(timedelta(hours=-6), "America/Guatemala")).isoformat()
    for name in ("pytest", "pytest-bdd", "selenium", "Flask"):
        ENVIRONMENT[name] = importlib.metadata.version(name)
    ENVIRONMENT["python"] = platform.python_version()
    rows = []
    for entry in sorted(RESULTS.values(), key=lambda e: e["id"]):
        phases = entry["phases"]
        entry["outcome"] = ("fallido" if any(p["outcome"] == "failed" for p in phases)
                            else "omitido" if any(p["outcome"] == "skipped" for p in phases)
                            else "aprobado" if any(p["phase"] == "call" for p in phases) else "no ejecutado")
        entry["cause"] = "\n".join(p["cause"] for p in phases if p["cause"])
        rows.append(entry)
    totals = {label: sum(r["outcome"] == label for r in rows)
              for label in ("aprobado", "fallido", "omitido", "no ejecutado")}
    payload = {"timestamp": timestamp, "exit_status": int(exitstatus), "environment": ENVIRONMENT,
               "totals": totals, "scenarios": rows}
    (REPORTS / "resultados.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Resultados del laboratorio BDD", "", f"Ejecución: {timestamp}", "",
             f"Resultado: {totals['aprobado']} aprobados, {totals['fallido']} fallidos, "
             f"{totals['omitido']} omitidos, {totals['no ejecutado']} no ejecutados.", "",
             f"Código de salida de pytest: {exitstatus}.", "",
             f"Datos reales y escenarios originales intactos: {ENVIRONMENT.get('real_data_unchanged', 'sin verificar')}.",
             "", "| Escenario | Resultado | Duración (s) |", "|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['id']} — {row['scenario']} | {row['outcome']} | {row['duration']:.2f} |")
    lines += ["", "## Entorno", ""]
    lines += [f"- {k}: {v}" for k, v in ENVIRONMENT.items() if "sha256" not in k]
    for row in rows:
        if row["cause"]:
            lines += ["", f"## Causa de {row['id']}", "", "```text", row["cause"], "```"]
    lines += ["", "Los escenarios API usan el cliente Flask; los de interfaz usan Chrome headless y "
              "un servidor local con datos temporales. Los hashes están en resultados.json. "
              "Los fallos de preparación se reportan como fallidos, nunca como aprobados u omitidos.", ""]
    (REPORTS / "resultados.md").write_text("\n".join(lines), encoding="utf-8")
