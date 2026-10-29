"""Dos escenarios Selenium; patrones de interacción de tests/bdd/test_edicion_rutas.py."""
from urllib.parse import parse_qs, urlparse

from pytest_bdd import given, when, then, scenarios
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

scenarios("features/crear_ruta.feature", "features/editar_ruta.feature")


def wait(ctx, condition):
    return WebDriverWait(ctx.driver, 15).until(condition)


def element(ctx, selector):
    return wait(ctx, EC.presence_of_element_located((By.CSS_SELECTOR, selector)))


def click(ctx, selector):
    wait(ctx, EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()


def fill(ctx, selector, text):
    field = element(ctx, selector)
    field.send_keys(Keys.CONTROL, "a")
    field.send_keys(text)
    field.send_keys(Keys.TAB)


def open_tab(ctx, selector):
    ctx.previous_handles = set(ctx.driver.window_handles)
    click(ctx, selector)


def route_selector(ctx):
    return f'#terminal a.edit-link[href*="route={ctx.route_id}"]'


def assert_values(ctx):
    wait(ctx, lambda d: d.find_element(By.ID, "routeNameInput").get_attribute("value")
         == ctx.expected_name)
    assert element(ctx, "#routeInstructionsInput").get_attribute("value") == ctx.expected_instructions


def assert_persisted(ctx):
    # Se lee el archivo temporal escrito por Flask; no basta el mensaje visual.
    saved = ctx.read()
    routes = saved["maps"]["terminal"]["routes"]
    matching = [r for r in routes if r["id"] == ctx.route_id]
    assert len(matching) == 1
    assert matching[0]["name"] == ctx.expected_name
    assert matching[0]["instructions"] == ctx.expected_instructions
    assert matching[0]["nodes"] == ctx.expected_nodes
    original = ctx.initial["maps"]["terminal"]["routes"]
    assert len(routes) == len(original) + (1 if ctx.creating else 0)
    assert [r for r in routes if r["id"] != ctx.route_id] == [
        r for r in original if r["id"] != ctx.route_id]
    assert {key: value for key, value in saved["maps"].items() if key != "terminal"} == {
        key: value for key, value in ctx.initial["maps"].items() if key != "terminal"}


@given("que el administrador está en el panel de rutas del mapa de oficinas")
def panel(ctx, browser):
    ctx.dashboard_handle = browser.current_window_handle
    browser.get(ctx.base_url + "/dashboard2#terminal")
    element(ctx, "#terminal a.new-route-link")


@given("que existe una ruta en el sistema de pruebas")
def existing(ctx, browser):
    panel(ctx, browser)
    ctx.creating = False
    route = next(r for r in ctx.initial["maps"]["terminal"]["routes"] if r["id"] == ctx.route_id)
    ctx.expected_nodes = route["nodes"]
    element(ctx, route_selector(ctx))


@when("selecciona Nueva ruta")
def new_route(ctx):
    ctx.creating = True
    open_tab(ctx, "#terminal a.new-route-link")


@when("el administrador selecciona Editar")
def edit_route(ctx):
    open_tab(ctx, route_selector(ctx))


@when("se abre el editor en una nueva pestaña")
def editor(ctx):
    wait(ctx, EC.number_of_windows_to_be(len(ctx.previous_handles) + 1))
    handle, = set(ctx.driver.window_handles) - ctx.previous_handles
    ctx.driver.switch_to.window(handle)
    expected = "Nueva ruta" if ctx.creating else next(
        r["name"] for r in ctx.initial["maps"]["terminal"]["routes"] if r["id"] == ctx.route_id)
    wait(ctx, lambda d: d.find_element(By.ID, "routeNameInput").get_attribute("value") == expected)
    query = parse_qs(urlparse(ctx.driver.current_url).query)
    assert query["scope"] == ["route"]
    if ctx.creating:
        assert query["new"] == ["1"]
    else:
        assert query["route"] == [ctx.route_id]


@when("escribe un nombre y unas indicaciones")
@when("modifica el nombre y las indicaciones")
def write_fields(ctx):
    ctx.expected_name = "Ruta de prueba BDD" if ctx.creating else "Oficina editada BDD"
    ctx.expected_instructions = "Avance por el pasillo hasta la oficina de pruebas."
    fill(ctx, "#routeNameInput", ctx.expected_name)
    fill(ctx, "#routeInstructionsInput", ctx.expected_instructions)


@when("conserva los dos nodos iniciales")
def initial_nodes(ctx):
    click(ctx, '[data-mode="nodes"]')
    rows = ctx.driver.find_elements(By.CSS_SELECTOR, "#nodeList .node-row")
    assert len(rows) == 2
    ctx.expected_nodes = [
        {axis: int(element(ctx, f'[data-node-index="{i}"][data-axis="{axis}"]').get_attribute("value"))
         for axis in ("x", "y")} for i in range(2)]
    assert ctx.expected_nodes == [{"x": 1000, "y": 700}, {"x": 1100, "y": 700}]
    assert ctx.read() == ctx.initial, "El borrador no debe persistirse antes de guardar"


@when("presiona Guardar")
def save(ctx):
    click(ctx, "#saveButton")


@then("el sistema confirma el guardado")
def confirmed(ctx):
    wait(ctx, lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado"
         and d.find_element(By.ID, "saveButton").is_enabled())
    if ctx.creating:
        ctx.route_id = parse_qs(urlparse(ctx.driver.current_url).query)["route"][0]
        assert ctx.route_id not in [r["id"] for r in ctx.initial["maps"]["terminal"]["routes"]]
    assert_persisted(ctx)


@then("la ruta aparece en el panel administrativo")
def appears(ctx):
    ctx.driver.switch_to.window(ctx.dashboard_handle)
    ctx.driver.refresh()
    edit = element(ctx, route_selector(ctx))
    row = edit.find_element(By.XPATH, "ancestor::tr")
    assert ctx.expected_name in row.text


@then("al abrirla nuevamente los datos se mantienen")
def reopen(ctx):
    previous = set(ctx.driver.window_handles)
    click(ctx, route_selector(ctx))
    wait(ctx, EC.number_of_windows_to_be(len(previous) + 1))
    handle, = set(ctx.driver.window_handles) - previous
    ctx.driver.switch_to.window(handle)
    assert_values(ctx)
    assert_persisted(ctx)


@then("al recargar el editor los cambios permanecen guardados")
def reload(ctx):
    ctx.driver.refresh()
    assert_values(ctx)
    assert_persisted(ctx)
