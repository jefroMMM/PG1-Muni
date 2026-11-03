"""Ejecutar desde la raíz: tests/seminario/.venv/Scripts/python.exe tests/gherkin/test_pruebas_administrativas.py
Instalar en ese entorno: python -m pip install pytest==8.3.5 pytest-bdd==8.1.0 selenium==4.35.0
Admite -k audio y --junitxml=RUTA. Usa Chrome sin ventana y datos temporales por caso.
BDD_CHROME_BINARY y BDD_CHROMEDRIVER permiten elegir ejecutables. No ejecutar en paralelo.
"""
import copy, hashlib, json, os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import urlopen

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pytest

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(pytest.main(["-v", "--tb=short", "-p", "no:cacheprovider", str(Path(__file__).resolve()), *sys.argv[1:]]))

from pytest_bdd import given, when, then, parsers, scenarios
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server

from backend.app import DEFAULT_CONFIG, create_app
from backend.storage import ConfigStore

scenarios("pruebas_administrativas.feature")

@pytest.fixture(scope="session", autouse=True)
def proteger_originales():
    def inventario():
        entries = list((ROOT / "data").rglob("*")) + [ROOT / "Audio de prueba.mp3"]
        return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                if p.is_file() else "directorio" for p in entries}
    antes = inventario()
    yield
    assert inventario() == antes, "Los datos originales o sus archivos cambiaron"

@pytest.fixture
def ctx(tmp_path):
    archivo = tmp_path / "data/routes-config.json"
    store = ConfigStore(lambda: archivo, lambda: DEFAULT_CONFIG)
    initial = store.load()
    app = create_app(store, tmp_path / "uploads")
    app.config["TESTING"] = True
    route = next(r for r in initial["maps"]["terminal"]["routes"] if not r.get("archived"))
    return SimpleNamespace(store=store, initial=initial, app=app, client=app.test_client(),
                           route_id=route["id"], config_path=archivo)

@pytest.fixture
def browser(ctx):
    server = make_server("127.0.0.1", 0, ctx.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    ctx.base_url = f"http://127.0.0.1:{server.server_port}"
    driver = None
    try:
        with urlopen(ctx.base_url + "/api/config", timeout=5) as response:
            assert response.status == 200
            assert json.load(response) == ctx.initial
        options = webdriver.ChromeOptions()
        for argument in ("--headless=new", "--window-size=1600,1100", "--disable-notifications"):
            options.add_argument(argument)
        options.set_capability("unhandledPromptBehavior", "accept")
        if os.environ.get("BDD_CHROME_BINARY"):
            options.binary_location = os.environ["BDD_CHROME_BINARY"]
        service = Service(os.environ["BDD_CHROMEDRIVER"]) if os.environ.get("BDD_CHROMEDRIVER") else Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        ctx.driver = driver
        yield driver
    finally:
        try:
            if driver is not None:
                driver.quit()
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
            assert not thread.is_alive(), "El servidor temporal no se cerró"

def wait(ctx, condition):
    return WebDriverWait(ctx.driver, 15, ignored_exceptions=(StaleElementReferenceException,)).until(condition)

def element(ctx, selector):
    return wait(ctx, EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

def click(ctx, selector):
    wait(ctx, EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()

def fill(ctx, selector, text):
    field = element(ctx, selector)
    field.send_keys(Keys.CONTROL, "a")
    field.send_keys(text, Keys.TAB)

def value(ctx, selector, expected):
    wait(ctx, lambda d: d.find_element(By.CSS_SELECTOR, selector).get_attribute("value") == expected)

def route(ctx):
    return next(r for r in ctx.store.load()["maps"]["terminal"]["routes"] if r["id"] == ctx.route_id)

def panel(ctx):
    ctx.driver.get(ctx.base_url + "/dashboard2#terminal")
    ctx.panel_handle = ctx.driver.current_window_handle
    element(ctx, f'#terminal tr[data-route-id="{ctx.route_id}"]')

def open_editor(ctx, selector):
    previous = set(ctx.driver.window_handles)
    click(ctx, selector)
    wait(ctx, EC.number_of_windows_to_be(len(previous) + 1))
    handle, = set(ctx.driver.window_handles) - previous
    ctx.driver.switch_to.window(handle)
    wait(ctx, lambda d: any(field.is_displayed() for field in
         d.find_elements(By.CSS_SELECTOR, "#routeNameInput, #backgroundSelect")))

def save(ctx):
    click(ctx, "#saveButton")
    wait(ctx, lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado"
         and d.find_element(By.ID, "saveButton").is_enabled())

def steps(ctx, texts):
    fields = ctx.driver.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea")
    while len(fields) > 1:
        click(ctx, "#instructionStepList .remove-instruction-step")
        fields = ctx.driver.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea")
    fill(ctx, "#instructionStepList textarea", texts[0])
    for index, text in enumerate(texts[1:], start=2):
        click(ctx, "#addInstructionStepButton")
        fill(ctx, f"#instructionStepList li:nth-child({index}) textarea", text)

def write_route(ctx, name, texts):
    ctx.expected_name, ctx.expected_steps = name, texts
    fill(ctx, "#routeNameInput", name)
    steps(ctx, texts)
    save(ctx)

def assert_steps(ctx, expected):
    wait(ctx, lambda d: [f.get_attribute("value") for f in
         d.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea")] == expected)

def public_view(ctx):
    ctx.driver.get(ctx.base_url + "/")
    wait(ctx, lambda d: len(d.find_elements(By.CSS_SELECTOR, "#routeControls button")) ==
         sum(not r.get("archived") for r in ctx.store.load()["maps"]["terminal"]["routes"]))

@given("que existe un sistema de pruebas con datos iniciales")
def initial_system(ctx):
    assert ctx.store.load() == ctx.initial

@given("que el administrador está en el panel de pruebas")
@given("que el administrador ve una ruta visible en el panel de pruebas")
def admin_panel(ctx, browser):
    assert not route(ctx).get("archived")
    panel(ctx)

@when(parsers.parse('crea una sección llamada "{name}"'))
def create_section(ctx, name):
    click(ctx, "#newSectionButton")
    fill(ctx, "#sectionName", name)
    click(ctx, "#createSectionButton")
    wait(ctx, lambda d: urlparse(d.current_url).fragment.startswith("seccion-"))
    ctx.section_key = urlparse(ctx.driver.current_url).fragment
    ctx.section_name = name

@then("la sección aparece en el panel y queda guardada sin cambiar los mapas anteriores")
def section_saved(ctx):
    assert ctx.section_name in element(ctx, f'[id="{ctx.section_key}"]').text
    saved = ctx.store.load()
    assert saved["maps"][ctx.section_key]["sectionName"] == ctx.section_name
    assert saved["maps"][ctx.section_key]["routes"] == []
    assert len(saved["maps"]) == len(ctx.initial["maps"]) + 1
    assert all(saved["maps"][key] == original for key, original in ctx.initial["maps"].items())
    ctx.driver.refresh()
    assert ctx.section_name in element(ctx, f'[id="{ctx.section_key}"]').text

@when("se solicita por API crear una sección con un nombre de 81 caracteres")
def long_section(ctx):
    ctx.response = ctx.client.post("/api/maps", json={"name": "A" * 81, "template": "terminal", "icon": "building"})

@then("se rechaza la solicitud y los datos permanecen iguales")
def long_rejected(ctx):
    assert ctx.response.status_code == 400
    assert ctx.response.get_json()["error"] == "Escribe un nombre de sección de hasta 80 caracteres"
    assert ctx.store.load() == ctx.initial

@given("que el administrador abre la configuración del mapa de oficinas")
def map_editor(ctx, browser):
    panel(ctx)
    open_editor(ctx, "#terminal .configure-map")
    element(ctx, "#backgroundSelect option")

@when(parsers.re(r"carga (?P<kind>un croquis y guarda el fondo|el audio de prueba y guarda la ruta)"))
def upload(ctx, kind):
    background = kind.startswith("un croquis")
    ctx.group, input_id, ctx.select_id = ("backgrounds", "backgroundUploadInput", "backgroundSelect") if background else ("audios", "audioUploadInput", "routeAudioSelect")
    ctx.source = ROOT / ("tests/seminario/fixtures/croquis.png" if background else "Audio de prueba.mp3")
    if background and not ctx.source.is_file():
        ctx.source = DEFAULT_CONFIG.parent / "recursos/Fondos/croquis-terminal-2000x1000.png"
    assert ctx.source.is_file(), f"Falta el archivo de prueba: {ctx.source.name}"
    element(ctx, f"#{input_id}").send_keys(str(ctx.source))
    wait(ctx, lambda d: len(ctx.store.load()["catalog"][ctx.group]) == len(ctx.initial["catalog"][ctx.group]) + 1)
    ctx.asset = ctx.store.load()["catalog"][ctx.group][-1]
    value(ctx, f"#{ctx.select_id}", ctx.asset["src"])
    save(ctx)

@then("el fondo permanece al recargar y el archivo cargado coincide con el original")
@then("el audio queda asociado después de recargar y se entrega sin cambios")
def asset_saved(ctx):
    background = ctx.group == "backgrounds"
    assert (ctx.store.load()["maps"]["terminal"]["background"] if background else route(ctx)["audio"]) == ctx.asset["src"]
    ctx.driver.refresh()
    value(ctx, f"#{ctx.select_id}", ctx.asset["src"])
    if background:
        wait(ctx, lambda d: d.find_element(By.ID, "editorMapImage").get_property("naturalWidth") > 0)
    response = ctx.client.get(ctx.asset["src"])
    assert response.status_code == 200
    assert response.data == ctx.source.read_bytes()
    if not background:
        path = ctx.config_path.parent / unquote(ctx.asset["src"]).lstrip("/")
        assert path.is_file()
        assert path.read_bytes() == ctx.source.read_bytes()

@when(parsers.parse('abre Nueva ruta y guarda "{name}" con dos puntos iniciales'))
def create_route(ctx, name):
    open_editor(ctx, "#terminal .new-route-link")
    value(ctx, "#routeNameInput", "Nueva ruta")
    write_route(ctx, name, ["Avance hacia la oficina de pruebas."])
    ctx.route_id = parse_qs(urlparse(ctx.driver.current_url).query)["route"][0]

@then("la nueva ruta queda guardada y puede abrirse desde el panel")
def new_route_saved(ctx):
    saved = route(ctx)
    assert saved["name"] == ctx.expected_name
    assert saved["instructionSteps"] == ctx.expected_steps
    assert saved["nodes"] == [{"x": 1000, "y": 700}, {"x": 1100, "y": 700}]
    assert ctx.store.load()["maps"]["terminal"]["routes"][:-1] == ctx.initial["maps"]["terminal"]["routes"]
    ctx.driver.switch_to.window(ctx.panel_handle)
    ctx.driver.refresh()
    selector = f'#terminal a.edit-link[href*="route={ctx.route_id}"]'
    assert ctx.expected_name in element(ctx, selector).find_element(By.XPATH, "ancestor::tr").text
    open_editor(ctx, selector)
    value(ctx, "#routeNameInput", ctx.expected_name)
    assert_steps(ctx, ctx.expected_steps)

@given("que el administrador abre una ruta existente en su editor")
def existing_editor(ctx, browser):
    panel(ctx)
    open_editor(ctx, f'#terminal a.edit-link[href*="route={ctx.route_id}"]')
    value(ctx, "#routeNameInput", route(ctx)["name"])

@when(parsers.parse('cambia su nombre a "{name}" y escribe nuevas indicaciones'))
def edit_route(ctx, name):
    write_route(ctx, name, ["Ingrese por el pasillo.", "Gire a la derecha hasta la oficina."])

@then("los cambios permanecen al recargar sin modificar las otras rutas y mapas")
def edited_saved(ctx):
    assert route(ctx)["name"] == ctx.expected_name
    assert route(ctx)["instructionSteps"] == ctx.expected_steps
    expected = copy.deepcopy(ctx.initial)
    expected["maps"]["terminal"]["routes"] = ctx.store.load()["maps"]["terminal"]["routes"]
    assert ctx.store.load() == expected
    originals = [r for r in ctx.initial["maps"]["terminal"]["routes"] if r["id"] != ctx.route_id]
    assert [r for r in expected["maps"]["terminal"]["routes"] if r["id"] != ctx.route_id] == originals
    ctx.driver.refresh()
    value(ctx, "#routeNameInput", ctx.expected_name)
    assert_steps(ctx, ctx.expected_steps)

@when("intenta guardar un nombre que solo contiene espacios")
def blank_name(ctx):
    fill(ctx, "#routeNameInput", "   ")
    click(ctx, "#saveButton")

@then("aparece el rechazo y se conservan los datos previamente guardados")
def blank_rejected(ctx):
    wait(ctx, lambda d: "La ruta necesita nombre" in d.find_element(By.ID, "saveStatus").text)
    assert element(ctx, "#saveButton").is_enabled()
    assert ctx.store.load() == ctx.initial

@when("escribe y guarda tres pasos de indicaciones")
def three_steps(ctx):
    ctx.expected_steps = ["Ingrese por la entrada.", "Continúe por el pasillo.", "Gire hasta la oficina."]
    steps(ctx, ctx.expected_steps)
    save(ctx)

@then("los tres pasos permanecen en el editor y se muestran al visitante")
def three_saved(ctx):
    assert route(ctx)["instructionSteps"] == ctx.expected_steps
    ctx.driver.refresh()
    assert_steps(ctx, ctx.expected_steps)
    public_view(ctx)
    click(ctx, f'#routeControls button[data-route-id="{ctx.route_id}"]')
    wait(ctx, lambda d: [e.text for e in d.find_elements(By.CSS_SELECTOR, "#panelContent li")] == ctx.expected_steps)

@given("que el administrador ve una ruta archivada en el panel de pruebas")
def archived_route(ctx, browser):
    response = ctx.client.patch(f"/api/maps/terminal/routes/{ctx.route_id}/status", json={"archived": True})
    assert response.status_code == 200
    assert route(ctx)["archived"] is True
    panel(ctx)
    assert element(ctx, f'#terminal tr[data-route-id="{ctx.route_id}"] .status-pill').text == "Archivada"

@when("pulsa Archivar para esa ruta")
@when("pulsa Restaurar para esa ruta")
def archive_action(ctx):
    ctx.before_action = ctx.store.load()
    click(ctx, f'#terminal tr[data-route-id="{ctx.route_id}"] [data-route-action="archive"]')

def assert_visibility(ctx, archived):
    label = "Archivada" if archived else "Visible"
    wait(ctx, lambda d: d.find_element(By.CSS_SELECTOR,
         f'#terminal tr[data-route-id="{ctx.route_id}"] .status-pill').text == label)
    expected = copy.deepcopy(ctx.before_action)
    next(r for r in expected["maps"]["terminal"]["routes"] if r["id"] == ctx.route_id)["archived"] = archived
    assert ctx.store.load() == expected
    public_view(ctx)
    buttons = ctx.driver.find_elements(By.CSS_SELECTOR, f'#routeControls button[data-route-id="{ctx.route_id}"]')
    assert bool(buttons) is (not archived)

@then("queda archivada en el panel y no aparece como botón en el visor público")
def archived_hidden(ctx):
    assert_visibility(ctx, True)

@then("queda visible en el panel y vuelve a aparecer como botón en el visor público")
def restored_visible(ctx):
    assert_visibility(ctx, False)
