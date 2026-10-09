"""Pasos del piloto original: interacción real con Selenium y contrato Flask."""
import copy
from urllib.parse import parse_qs, urlparse

from pytest_bdd import given, when, then, scenarios
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from backend import app as backend

scenarios("features/edicion_rutas_administrativas.feature")


def wait(ctx, condition):
    return WebDriverWait(ctx.driver, 15).until(condition)


def el(ctx, selector):
    return wait(ctx, EC.presence_of_element_located((By.CSS_SELECTOR, selector)))


def click(ctx, selector):
    wait(ctx, EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()


def mode(ctx, value):
    click(ctx, f'[data-mode="{value}"]')


def fill(ctx, selector, value):
    field = el(ctx, selector)
    field.send_keys(Keys.CONTROL, "a")
    field.send_keys(str(value))
    field.send_keys(Keys.TAB)


def dashboard(ctx):
    if not hasattr(ctx, "dashboard_handle"):
        ctx.dashboard_handle = ctx.driver.current_window_handle
    ctx.driver.switch_to.window(ctx.dashboard_handle)
    ctx.driver.get(ctx.base_url + "/dashboard2")
    el(ctx, f'a.edit-link[href*="route={ctx.route_id}"]')


def open_editor(ctx):
    dashboard(ctx)
    previous = set(ctx.driver.window_handles)
    click(ctx, f'a.edit-link[href*="route={ctx.route_id}"]')
    wait(ctx, lambda d: len(set(d.window_handles) - previous) == 1)
    ctx.editor_handle = (set(ctx.driver.window_handles) - previous).pop()
    ctx.driver.switch_to.window(ctx.editor_handle)
    wait(ctx, lambda d: d.find_element(By.ID, "routeNameInput").get_attribute("value") == ctx.route()["name"])


def visitor(ctx):
    if not hasattr(ctx, "viewer_handle"):
        ctx.driver.switch_to.new_window("tab")
        ctx.viewer_handle = ctx.driver.current_window_handle
    ctx.driver.switch_to.window(ctx.viewer_handle)
    ctx.driver.get(ctx.base_url + "/")
    wait(ctx, lambda d: len(d.find_elements(By.CSS_SELECTOR, "#routeControls button")) > 0)


def save(ctx):
    count = len(ctx.web_responses)
    click(ctx, "#saveButton")
    wait(ctx, lambda d: len(ctx.web_responses) > count and d.find_element(By.ID, "saveButton").is_enabled())


def saved(ctx):
    wait(ctx, lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado")


def node_values(ctx):
    return [{axis: int(el(ctx, f'[data-node-index="{i}"][data-axis="{axis}"]').get_attribute("value"))
             for axis in ("x", "y")}
            for i in range(len(ctx.driver.find_elements(By.CSS_SELECTOR, "#nodeList .node-row")))]


def patch(ctx, route, **extra):
    return ctx.client.patch(f"/api/maps/{ctx.map_key}/routes/{ctx.route_id}", json={"route": route, **extra})


@given('que el panel administrativo "/dashboard2" muestra una ruta existente del mapa de oficinas')
def panel_exists(ctx, browser):
    dashboard(ctx)


@when('el personal pulsa "Editar" en esa ruta')
def edit_link(ctx):
    open_editor(ctx)


@then('se abre una nueva pestaña con el identificador de esa ruta y el parámetro "scope=route"')
def correct_tab(ctx):
    assert ctx.editor_handle != ctx.dashboard_handle
    query = parse_qs(urlparse(ctx.driver.current_url).query)
    assert query["route"] == [ctx.route_id] and query["scope"] == ["route"]


@then('se muestran sus datos guardados y los modos "Nodos", "Assets" y "Texto y audio"')
def editor_data(ctx):
    route = ctx.route()
    assert el(ctx, "#routeNameInput").get_attribute("value") == route["name"]
    assert el(ctx, "#routeInstructionsInput").get_attribute("value") == route["instructions"]
    assert Select(el(ctx, "#routeAudioSelect")).first_selected_option.get_attribute("value") == route["audio"]
    assert el(ctx, "#routeColorInput").get_attribute("value") == route["buttonColor"]
    for value in ("nodes", "assets", "text-audio"):
        assert el(ctx, f'[data-mode="{value}"]').is_displayed()
    mode(ctx, "nodes")
    assert node_values(ctx) == route["nodes"]


@then('se ofrece la acción "Archivar" o "Desarchivar" según el estado de la ruta')
def archive_action(ctx):
    assert el(ctx, "#archiveRouteButton").text == ("Desarchivar" if ctx.route()["archived"] else "Archivar")


@then('están ocultos los modos "Mapa", "Iconos" y "Decoraciones"')
def map_modes_hidden(ctx):
    for value in ("map", "icons", "decorations"):
        assert not el(ctx, f'[data-mode="{value}"]').is_displayed()


@then('están ocultas las acciones para crear, duplicar y borrar rutas')
def actions_hidden(ctx):
    for selector in ("#newRouteButton", "#duplicateRouteButton", "#deleteRouteButton"):
        assert not el(ctx, selector).is_displayed()


@given('que una ruta visible está abierta desde el panel en su editor individual')
@given('que una ruta visible está abierta en su editor individual')
@given('que una ruta existente está abierta en su editor individual')
def existing_editor(ctx, browser):
    assert not ctx.route()["archived"]
    open_editor(ctx)


@given('que su catálogo contiene el recurso de recorrido "footprints-auto"')
def catalog_asset(ctx):
    assert any(a["id"] == "footprints-auto" for a in ctx.read()["catalog"]["routeAssets"])


@when('el personal modifica sus campos con estos valores')
def edit_fields(ctx, datatable):
    values = dict(datatable[1:])
    mode(ctx, "text-audio")
    for name, selector in (("Nombre", "#routeNameInput"), ("Indicaciones", "#routeInstructionsInput")):
        fill(ctx, selector, values[name])
    # Un control de color nativo no permite escribir texto consistentemente entre SO.
    # Solo se modifica el control y se dispara su evento público; no el estado de la app.
    ctx.driver.execute_script("arguments[0].value=arguments[1]; arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                              el(ctx, "#routeColorInput"), values["Color de boton"])
    Select(el(ctx, "#routeAudioSelect")).select_by_visible_text(values["Audio de esta ruta"])
    mode(ctx, "assets")
    fill(ctx, "#routeAssetSizeInput", values["Tamano de assets"])
    ctx.expected.update(name=values["Nombre"], instructions=values["Indicaciones"],
                        buttonColor=values["Color de boton"], assetSize=int(values["Tamano de assets"]), audio="")


@when('agrega un nodo en las coordenadas 1200 y 700')
def add_node(ctx):
    mode(ctx, "nodes")
    count = len(node_values(ctx))
    click(ctx, "#addNodeButton")
    svg = el(ctx, "#editorLayer")
    # getBoundingClientRect conserva las fracciones que WebElement.rect redondea.
    rect = ctx.driver.execute_script("const r=arguments[0].getBoundingClientRect();return {w:r.width,h:r.height};", svg)
    dx, dy = round(rect["w"] * (1200 / 2000 - .5)), round(rect["h"] * (700 / 1000 - .5))
    ActionChains(ctx.driver).move_to_element(svg).move_by_offset(dx, dy).click().perform()
    wait(ctx, lambda d: len(d.find_elements(By.CSS_SELECTOR, "#nodeList .node-row")) == count + 1)
    # Ajuste preciso a través de los campos públicos tras el clic físico sobre el mapa.
    fill(ctx, f'[data-node-index="{count}"][data-axis="x"]', 1200)
    fill(ctx, f'[data-node-index="{count}"][data-axis="y"]', 700)
    assert node_values(ctx)[-1] == {"x": 1200, "y": 700}


@when('mueve el primer nodo a las coordenadas 900 y 650')
def move_node(ctx):
    fill(ctx, '[data-node-index="0"][data-axis="x"]', 900)
    fill(ctx, '[data-node-index="0"][data-axis="y"]', 650)
    ctx.expected["nodes"] = node_values(ctx)


@when('asigna el recurso "footprints-auto" al primer tramo')
def segment_asset(ctx):
    mode(ctx, "assets")
    Select(el(ctx, '[data-segment-index="0"]')).select_by_value("footprints-auto")


@when('pulsa una vez "Espejo" y una vez la rotación del primer tramo inicialmente sin transformaciones')
def transform_segment(ctx):
    assert "active" not in el(ctx, '[data-segment-mirror="0"]').get_attribute("class")
    assert el(ctx, '[data-segment-rotate="0"]').text == "0 deg"
    click(ctx, '[data-segment-mirror="0"]')
    click(ctx, '[data-segment-rotate="0"]')


@when('pulsa "Guardar"')
def click_save(ctx):
    save(ctx)


@then('el estado del editor muestra "Guardado"')
@then('el editor muestra "Guardado"')
def successful_save(ctx):
    saved(ctx)
    assert ctx.web_responses[-1]["status"] == 200


@then('al recargar el editor se conservan los campos y nodos modificados')
def persisted_fields(ctx):
    ctx.driver.refresh()
    wait(ctx, lambda d: d.find_element(By.ID, "routeNameInput").get_attribute("value") == ctx.expected["name"])
    route = ctx.route()
    for key, value in ctx.expected.items():
        assert route[key] == value, key
    assert el(ctx, "#routeInstructionsInput").get_attribute("value") == ctx.expected["instructions"]
    assert el(ctx, "#routeColorInput").get_attribute("value") == ctx.expected["buttonColor"]
    assert Select(el(ctx, "#routeAudioSelect")).first_selected_option.get_attribute("value") == ""
    mode(ctx, "assets")
    assert int(el(ctx, "#routeAssetSizeInput").get_attribute("value")) == ctx.expected["assetSize"]
    mode(ctx, "nodes")
    assert node_values(ctx) == ctx.expected["nodes"]


@then('el primer tramo conserva el recurso elegido, el efecto espejo y una rotación de 45 grados')
def persisted_segment(ctx):
    route = ctx.route()
    assert route["segmentAssets"][0] == "footprints-auto"
    assert route["segmentOptions"][0] == {"rotation": 45, "mirrored": True}
    mode(ctx, "assets")
    assert Select(el(ctx, '[data-segment-index="0"]')).first_selected_option.get_attribute("value") == "footprints-auto"
    assert "active" in el(ctx, '[data-segment-mirror="0"]').get_attribute("class")
    assert el(ctx, '[data-segment-rotate="0"]').text == "45 deg"


@then('al seleccionar la ruta en el visor se muestran el nuevo nombre y las nuevas indicaciones')
def changed_visitor(ctx):
    visitor(ctx)
    button = el(ctx, f'#routeControls button[data-route-id="{ctx.route_id}"]')
    assert button.text == ctx.expected["name"]
    button.click()
    assert el(ctx, "#panelContent h1").text == ctx.expected["name"]
    steps = [e.text for e in ctx.driver.find_elements(By.CSS_SELECTOR, "#panelContent ol li")]
    assert steps == ["Avance por el pasillo", "Gire a la derecha"]


@then('el fondo, los iconos, las decoraciones y las demás rutas permanecen como estaban')
def other_data_unchanged(ctx):
    current = ctx.read()
    expected = copy.deepcopy(ctx.initial)
    expected["maps"][ctx.map_key]["routes"][0] = ctx.route()
    assert current == expected


@when('el personal pulsa "Archivar" y guarda la ruta')
def archive(ctx):
    click(ctx, "#archiveRouteButton")
    save(ctx)
    saved(ctx)


@then('al recargar el visor no aparece el botón de esa ruta')
def visitor_archived(ctx):
    visitor(ctx)
    assert not ctx.driver.find_elements(By.CSS_SELECTOR, f'#routeControls [data-route-id="{ctx.route_id}"]')


@then('el panel administrativo sigue mostrando la ruta con estado "Archivada"')
def dashboard_archived(ctx):
    dashboard(ctx)
    row = el(ctx, f'a.edit-link[href*="route={ctx.route_id}"]').find_element(By.XPATH, "ancestor::tr")
    assert row.find_element(By.CSS_SELECTOR, ".status-pill").text == "Archivada"


@when('el personal vuelve a abrir esa ruta desde el panel, pulsa "Desarchivar" y guarda')
def unarchive(ctx):
    open_editor(ctx)
    assert el(ctx, "#archiveRouteButton").text == "Desarchivar"
    click(ctx, "#archiveRouteButton")
    save(ctx)
    saved(ctx)


@then('al recargar el visor vuelve a aparecer el botón de esa ruta')
def visitor_visible(ctx):
    visitor(ctx)
    assert el(ctx, f'#routeControls [data-route-id="{ctx.route_id}"]').is_displayed()


@then('el panel administrativo muestra la ruta con estado "Visible" al actualizarse')
def dashboard_visible(ctx):
    dashboard(ctx)
    row = el(ctx, f'a.edit-link[href*="route={ctx.route_id}"]').find_element(By.XPATH, "ancestor::tr")
    assert row.find_element(By.CSS_SELECTOR, ".status-pill").text == "Visible"


@given('que el personal cambia el nombre a "Recorrido en revisión" y las indicaciones a "Siga el recorrido de prueba."')
def preview_draft(ctx):
    fill(ctx, "#routeNameInput", "Recorrido en revisión")
    fill(ctx, "#routeInstructionsInput", "Siga el recorrido de prueba.")


@when('pulsa "Previsualizar ruta"')
def preview(ctx):
    click(ctx, "#previewButton")


@then('la vista previa muestra el recorrido animado y los textos del borrador')
def preview_content(ctx):
    wait(ctx, EC.frame_to_be_available_and_switch_to_it((By.ID, "previewFrame")))
    wait(ctx, lambda d: d.find_element(By.CSS_SELECTOR, "#panelContent h1").text == "Recorrido en revisión")
    assert el(ctx, "#panelContent li").text == "Siga el recorrido de prueba"
    footprints = ctx.driver.find_elements(By.CSS_SELECTOR, "#routeFootprints .route-footprint")
    assert footprints
    assert any(float(e.get_attribute("x")) > 0 for e in footprints)
    animation = ctx.driver.execute_script("return getComputedStyle(arguments[0]).animationName;", footprints[0])
    assert animation and animation != "none"
    ctx.driver.switch_to.default_content()


@then('la configuración persistida conserva el nombre y las indicaciones anteriores')
def draft_not_persisted(ctx):
    assert ctx.read() == ctx.initial
    assert not ctx.web_responses


@when('pulsa "Volver a editar"')
def close_preview(ctx):
    click(ctx, "#closePreviewButton")


@then('el editor conserva el borrador y muestra "Cambios sin guardar"')
def draft_preserved(ctx):
    assert not el(ctx, "#previewDialog").is_displayed()
    assert el(ctx, "#routeNameInput").get_attribute("value") == "Recorrido en revisión"
    assert el(ctx, "#routeInstructionsInput").get_attribute("value") == "Siga el recorrido de prueba."
    assert el(ctx, "#saveStatus").text == "Cambios sin guardar"


@when('el personal reemplaza el nombre por tres espacios y pulsa "Guardar"')
def blank_name(ctx):
    fill(ctx, "#routeNameInput", "   ")
    save(ctx)


@then('la solicitud de actualización recibe el código HTTP 400')
def rejected_status(ctx):
    assert ctx.web_responses[-1]["status"] == 400
    assert ctx.web_responses[-1]["path"] == f"/api/maps/{ctx.map_key}/routes/{ctx.route_id}"


@then('el editor muestra "La ruta necesita nombre y al menos dos nodos dentro del mapa"')
def rejection_message(ctx):
    assert el(ctx, "#saveStatus").text == "La ruta necesita nombre y al menos dos nodos dentro del mapa"


@then('el botón "Guardar" vuelve a estar habilitado')
def save_enabled(ctx):
    assert el(ctx, "#saveButton").is_enabled()


@then('la configuración persistida conserva la ruta anterior')
def rejection_no_changes(ctx):
    assert ctx.read() == ctx.initial


@then('el editor conserva el nombre vacío resultante de quitar los espacios')
def blank_draft(ctx):
    # La app recorta el modelo, pero no reescribe el input en cada pulsación.
    # Se consulta la representación del borrador enviada a la previsualización.
    assert el(ctx, "#routeNameInput").get_attribute("value").strip() == ""
    click(ctx, "#previewButton")
    wait(ctx, EC.frame_to_be_available_and_switch_to_it((By.ID, "previewFrame")))
    wait(ctx, lambda d: len(d.find_elements(By.CSS_SELECTOR, "#routeControls button")) == 1)
    assert el(ctx, "#routeControls button").text == ""
    ctx.driver.switch_to.default_content()
    click(ctx, "#closePreviewButton")
    assert ctx.read() == ctx.initial


@given('que una ruta abierta en su editor individual tiene exactamente tres nodos')
def three_nodes(ctx, browser):
    seed = copy.deepcopy(ctx.initial)
    route = seed["maps"][ctx.map_key]["routes"][0]
    route["nodes"] = [{"x": 900, "y": 650}, {"x": 1000, "y": 650}, {"x": 1100, "y": 650}]
    route["segmentAssets"] = ["footprints-auto", "footprints-auto"]
    route["segmentOptions"] = [{"rotation": 0, "mirrored": False}] * 2
    backend.save_config(seed)
    ctx.initial = copy.deepcopy(seed)
    open_editor(ctx)
    mode(ctx, "nodes")
    assert len(node_values(ctx)) == 3


@when('el personal pulsa "Borrar ultimo" en el modo "Nodos"')
@when('vuelve a pulsar "Borrar ultimo"')
def delete_node(ctx):
    click(ctx, "#deleteNodeButton")


@then('la ruta queda con dos nodos y un tramo')
def minimum_nodes(ctx):
    assert len(node_values(ctx)) == 2
    ctx.minimum = node_values(ctx)
    mode(ctx, "assets")
    assert len(ctx.driver.find_elements(By.CSS_SELECTOR, "[data-segment-index]")) == 1
    mode(ctx, "nodes")


@then('se conservan los mismos dos nodos y el mismo tramo')
def still_minimum(ctx):
    assert node_values(ctx) == ctx.minimum
    mode(ctx, "assets")
    assert len(ctx.driver.find_elements(By.CSS_SELECTOR, "[data-segment-index]")) == 1
    mode(ctx, "nodes")


@then('al recargar la ruta conserva esos dos nodos')
def minimum_persisted(ctx):
    ctx.driver.refresh()
    el(ctx, "#routeNameInput")
    mode(ctx, "nodes")
    assert node_values(ctx) == ctx.minimum
    assert ctx.route()["nodes"] == ctx.minimum
    assert len(ctx.route()["segmentAssets"]) == 1


@when('el personal introduce -1 en X y 1001 en Y del primer nodo y confirma cada cambio')
def first_outside(ctx):
    mode(ctx, "nodes")
    fill(ctx, '[data-node-index="0"][data-axis="x"]', -1)
    fill(ctx, '[data-node-index="0"][data-axis="y"]', 1001)


@when('introduce 2001 en X y -1 en Y del segundo nodo y confirma cada cambio')
def second_outside(ctx):
    fill(ctx, '[data-node-index="1"][data-axis="x"]', 2001)
    fill(ctx, '[data-node-index="1"][data-axis="y"]', -1)


@then('el primer nodo queda en las coordenadas 0 y 1000')
def first_clamped(ctx):
    assert node_values(ctx)[0] == {"x": 0, "y": 1000}


@then('el segundo nodo queda en las coordenadas 2000 y 0')
def second_clamped(ctx):
    assert node_values(ctx)[1] == {"x": 2000, "y": 0}


@then('al recargar se conservan las coordenadas ajustadas en los bordes del mapa')
def bounds_persisted(ctx):
    ctx.driver.refresh()
    el(ctx, "#routeNameInput")
    mode(ctx, "nodes")
    first_clamped(ctx)
    second_clamped(ctx)
    assert ctx.route()["nodes"][:2] == [{"x": 0, "y": 1000}, {"x": 2000, "y": 0}]


@given('que existe una ruta válida en una configuración aislada')
def valid_api_route(ctx):
    assert backend.valid_route(ctx.route(), ctx.route_id)


@when('se envía por separado cada una de estas modificaciones al servicio PATCH de esa ruta')
def invalid_requests(ctx, datatable):
    for description, status, message in datatable[1:]:
        payload = {"route": copy.deepcopy(ctx.route())}
        route = payload["route"]
        if description == "falta el objeto route":
            payload = {}
        elif description == "el id de route difiere del identificador de la URL":
            route["id"] = "otra-ruta"
        elif description == "nodes contiene un solo nodo":
            route["nodes"] = route["nodes"][:1]
        elif description == "el primer nodo tiene x igual a -1":
            route["nodes"][0]["x"] = -1
        elif description == "el primer nodo tiene y igual a 1001":
            route["nodes"][0]["y"] = 1001
        elif description == "el primer nodo tiene x como texto JSON en vez de número":
            route["nodes"][0]["x"] = "900"
        elif description == "catalog.audios es un objeto en vez de una lista":
            payload["catalog"] = {"audios": {}}
        else:
            raise AssertionError(f"Variación no implementada: {description}")
        response = ctx.client.patch(f"/api/maps/{ctx.map_key}/routes/{ctx.route_id}", json=payload)
        ctx.results.append((description, response.status_code, response.get_json(), int(status), message, ctx.read()))


@then('cada respuesta contiene el código y el mensaje indicados')
def api_errors(ctx):
    assert len(ctx.results) == 7
    for description, actual_status, body, expected_status, message, _ in ctx.results:
        assert actual_status == expected_status, description
        assert body == {"error": message}, description


@then('después de cada solicitud la configuración persistida permanece intacta')
def api_unchanged(ctx):
    for description, *_, snapshot in ctx.results:
        assert snapshot == ctx.initial, description


@given('que dos editores individuales cargaron la misma configuración con dos rutas distintas')
def two_snapshots(ctx):
    first = ctx.client.get("/api/config").get_json()
    second = ctx.client.get("/api/config").get_json()
    assert first == second
    ctx.first_route = copy.deepcopy(first["maps"][ctx.map_key]["routes"][0])
    ctx.second_route = copy.deepcopy(second["maps"][ctx.map_key]["routes"][1])
    assert ctx.first_route["id"] != ctx.second_route["id"]


@given('que el primer editor cambia el nombre de la primera ruta')
def edit_first(ctx):
    ctx.first_route["name"] = "Nombre actualizado desde primera ventana"


@given('que el segundo editor cambia las indicaciones de la segunda ruta sin recargar la configuración')
def edit_second(ctx):
    ctx.second_route["instructions"] = "Indicaciones actualizadas desde segunda ventana."


@when('se guarda primero la primera ruta y después la segunda mediante sus solicitudes PATCH')
def save_two(ctx):
    ctx.responses = [ctx.client.patch(f"/api/maps/{ctx.map_key}/routes/{route['id']}", json={"route": route})
                     for route in (ctx.first_route, ctx.second_route)]


@then('ambas respuestas tienen código HTTP 200 y el campo ok igual a verdadero')
def both_saved(ctx):
    assert all(r.status_code == 200 and r.get_json() == {"ok": True} for r in ctx.responses)


@then('la configuración persistida contiene el nuevo nombre de la primera ruta y las nuevas indicaciones de la segunda')
def both_changes(ctx):
    routes = ctx.read()["maps"][ctx.map_key]["routes"]
    assert routes[0]["name"] == ctx.first_route["name"]
    assert routes[1]["instructions"] == ctx.second_route["instructions"]


@then('se conservan los fondos, los iconos, las decoraciones y las rutas de los demás mapas')
def maps_unchanged(ctx):
    expected = copy.deepcopy(ctx.initial)
    expected["maps"][ctx.map_key]["routes"][0]["name"] = ctx.first_route["name"]
    expected["maps"][ctx.map_key]["routes"][1]["instructions"] = ctx.second_route["instructions"]
    assert ctx.read() == expected


@given('que el editor individual cargó una ruta válida de un mapa existente')
def loaded_then_missing(ctx):
    data = ctx.client.get("/api/config").get_json()
    ctx.loaded_route = copy.deepcopy(data["maps"][ctx.map_key]["routes"][0])
    assert backend.valid_route(ctx.loaded_route, ctx.route_id)


@given('que un cambio externo en la configuración aislada eliminó únicamente esa ruta')
def external_delete(ctx):
    config = ctx.read()
    config["maps"][ctx.map_key]["routes"] = [r for r in config["maps"][ctx.map_key]["routes"] if r["id"] != ctx.route_id]
    backend.save_config(config)


@given('que se registró la configuración persistida después de esa eliminación')
def snapshot_after_delete(ctx):
    ctx.after_delete = ctx.read()


@when('se envía la solicitud PATCH de guardado con los datos válidos del editor y el identificador original')
def missing_patch(ctx):
    ctx.response = patch(ctx, ctx.loaded_route)


@then('el servicio responde con código HTTP 404 y el mensaje "Ruta no encontrada"')
def not_found(ctx):
    assert ctx.response.status_code == 404
    assert ctx.response.get_json() == {"error": "Ruta no encontrada"}


@then('la configuración persistida permanece igual a la registrada después de la eliminación')
def no_resurrection_changes(ctx):
    assert ctx.read() == ctx.after_delete


@then('no se vuelve a crear la ruta eliminada')
def no_resurrection(ctx):
    assert all(r["id"] != ctx.route_id for r in ctx.read()["maps"][ctx.map_key]["routes"])
