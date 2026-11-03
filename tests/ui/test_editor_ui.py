"""Browser regression checks against temporary configuration and uploads."""
import threading
import time
import shutil
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from werkzeug.serving import make_server

from backend.app import DEFAULT_CONFIG, create_app
from backend.storage import ConfigStore

REPORTS = Path(__file__).parent / "reports"


@pytest.fixture
def browser(tmp_path):
    store = ConfigStore(lambda: tmp_path / "config.json", lambda: DEFAULT_CONFIG)
    application = create_app(store, tmp_path / "uploads")
    server = make_server("127.0.0.1", 0, application, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        REPORTS.mkdir(exist_ok=True)
        yield driver, f"http://127.0.0.1:{server.server_port}", store
    finally:
        if driver is not None:
            driver.quit()
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def replace(field, value):
    field.send_keys(Keys.CONTROL, "a")
    field.send_keys(value)


@pytest.mark.parametrize("map_key,editor", [("terminal", "/Conf"), ("mapar", "/MapaR/Conf")])
def test_steps_duration_area_and_preview(browser, map_key, editor):
    driver, base, store = browser
    route_id = store.load()["maps"][map_key]["routes"][0]["id"]
    wait = WebDriverWait(driver, 12)
    driver.get(f"{base}{editor}?scope=route&route={route_id}")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea"))
    while len(driver.find_elements(By.CSS_SELECTOR, ".remove-instruction-step")) > 1:
        driver.find_element(By.CSS_SELECTOR, ".remove-instruction-step").click()
    replace(driver.find_element(By.CSS_SELECTOR, "#instructionStepList textarea"), "Cruza el patio. Gira a la derecha.")
    driver.find_element(By.ID, "addInstructionStepButton").click()
    driver.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea")[-1].send_keys("Llegaste a tu destino.")
    replace(driver.find_element(By.ID, "routeDurationInput"), "3")
    driver.find_element(By.CSS_SELECTOR, '[data-mode="area"]').click()
    driver.find_element(By.ID, "drawAreaButton").click()
    svg = driver.find_element(By.ID, "editorLayer")
    for x, y in ((100, 100), (800, 100), (800, 500), (100, 500)):
        offset = driver.execute_script("""
            const svg = arguments[0], p = svg.createSVGPoint();
            p.x = arguments[1]; p.y = arguments[2];
            const screen = p.matrixTransform(svg.getScreenCTM());
            const box = svg.getBoundingClientRect();
            return [screen.x - box.left - box.width / 2, screen.y - box.top - box.height / 2];
        """, svg, x, y)
        ActionChains(driver).move_to_element_with_offset(svg, round(offset[0]), round(offset[1])).click().perform()
    assert len(driver.find_elements(By.CSS_SELECTOR, "#areaPointList input")) == 8
    assert len(driver.find_elements(By.CSS_SELECTOR, ".editor-area-handle")) == 4
    driver.save_screenshot(str(REPORTS / f"{map_key}-editor-desktop.png"))
    driver.find_element(By.ID, "saveButton").click()
    wait.until(lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado")
    saved = next(route for route in store.load()["maps"][map_key]["routes"] if route["id"] == route_id)
    assert saved["instructionSteps"] == ["Cruza el patio. Gira a la derecha.", "Llegaste a tu destino."]
    assert saved["durationSeconds"] == 3
    assert saved["highlightPolygon"]
    driver.refresh()
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea"))
    assert driver.find_element(By.ID, "routeDurationInput").get_attribute("value") == "3"
    driver.find_element(By.ID, "previewButton").click()
    driver.switch_to.frame(driver.find_element(By.ID, "previewFrame"))
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".route-active"))
    assert len(driver.find_elements(By.CSS_SELECTOR, "#panelContent li")) == 2
    start = time.monotonic()
    wait.until(lambda d: not d.find_elements(By.CSS_SELECTOR, ".route-active"))
    wait.until(lambda d: float(d.execute_script("return getComputedStyle(document.getElementById('panelLogo')).opacity")) > 0.99)
    assert time.monotonic() - start < 5
    driver.switch_to.default_content()
    driver.find_element(By.ID, "closePreviewButton").click()
    driver.set_window_size(390, 844)
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
    })
    assert driver.execute_script("return document.documentElement.scrollWidth <= innerWidth")
    driver.save_screenshot(str(REPORTS / f"{map_key}-editor-mobile.png"))
    errors = [entry for entry in driver.get_log("browser") if entry["level"] == "SEVERE" and "favicon.ico" not in entry["message"]]
    assert not errors, errors


def test_map_labels_are_text_and_assets_remain_available(browser):
    driver, base, store = browser
    data = store.load()
    data["maps"]["terminal"]["markers"] = [{
        "id": "quoted-marker", "assetId": data["catalog"]["markerIcons"][0]["id"],
        "label": 'Oficina "central" <img id="injected">', "x": 100, "y": 100, "width": 50, "height": 50
    }]
    store.save(data)
    driver.get(f"{base}/Conf?scope=map")
    wait = WebDriverWait(driver, 12)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#markerList input[data-field='label']"))
    driver.find_element(By.CSS_SELECTOR, '[data-mode="icons"]').click()
    label = driver.find_element(By.CSS_SELECTOR, "#markerList input[data-field='label']")
    assert label.get_attribute("value") == data["maps"]["terminal"]["markers"][0]["label"]
    assert not driver.find_elements(By.ID, "injected")
    driver.find_element(By.CSS_SELECTOR, '#markerList [data-item-action="mirror"]').click()
    driver.find_element(By.CSS_SELECTOR, '#markerList [data-item-action="rotate"]').click()
    driver.find_element(By.ID, "saveButton").click()
    wait.until(lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado")
    marker = store.load()["maps"]["terminal"]["markers"][0]
    assert marker["mirrored"] and marker["rotation"] == 45
    driver.get(f"{base}/dashboard2")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "a.edit-link"))
    driver.save_screenshot(str(REPORTS / "dashboard-desktop.png"))
    assert driver.execute_script("return Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)")


def test_resource_filters_preserve_cross_section_selections(browser):
    driver, base, store = browser
    config = store.load()
    route_id = config["maps"]["terminal"]["routes"][0]["id"]
    driver.get(f"{base}/Conf?scope=route&route={route_id}")
    wait = WebDriverWait(driver, 12)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea"))
    driver.find_element(By.CSS_SELECTOR, '[data-mode="assets"]').click()
    segment = driver.find_element(By.CSS_SELECTOR, "#segmentAssetList select")
    assert {option.get_attribute("value") for option in Select(segment).options} == {"footprints-auto"}
    Select(driver.find_element(By.ID, "routeAssetScope")).select_by_value("all")
    segment = driver.find_element(By.CSS_SELECTOR, "#segmentAssetList select")
    assert len(Select(segment).options) == len(config["catalog"]["routeAssets"])
    Select(segment).select_by_value("tuc-right")
    Select(driver.find_element(By.ID, "routeAssetScope")).select_by_value("section")
    assert driver.find_element(By.CSS_SELECTOR, "#segmentAssetList select").get_attribute("value") == "tuc-right"
    driver.find_element(By.CSS_SELECTOR, '[data-mode="text-audio"]').click()
    Select(driver.find_element(By.ID, "audioScope")).select_by_value("all")
    external_audio = next(asset["src"] for asset in config["catalog"]["audios"] if asset["sectionId"] == "mapar")
    Select(driver.find_element(By.ID, "routeAudioSelect")).select_by_value(external_audio)
    Select(driver.find_element(By.ID, "audioScope")).select_by_value("section")
    assert driver.find_element(By.ID, "routeAudioSelect").get_attribute("value") == external_audio
    driver.find_element(By.ID, "saveButton").click()
    wait.until(lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado")
    driver.refresh()
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea"))
    assert driver.find_element(By.ID, "routeAudioSelect").get_attribute("value") == external_audio
    route = next(route for route in store.load()["maps"]["terminal"]["routes"] if route["id"] == route_id)
    assert route["segmentAssets"][0] == "tuc-right"
    assert route["audio"] == external_audio
    driver.get(f"{base}/Conf?scope=map")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#markerAssetSelect option"))
    driver.find_element(By.CSS_SELECTOR, '[data-mode="icons"]').click()
    assert len(Select(driver.find_element(By.ID, "markerAssetSelect")).options) == 1
    Select(driver.find_element(By.ID, "markerScope")).select_by_value("all")
    assert len(Select(driver.find_element(By.ID, "markerAssetSelect")).options) == 3
    driver.save_screenshot(str(REPORTS / "resource-library-all.png"))
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
    })
    driver.execute_script("document.querySelector('.config-panel').scrollIntoView({block:'start'})")
    assert driver.execute_script("return document.documentElement.scrollWidth <= innerWidth")
    driver.save_screenshot(str(REPORTS / "resource-library-mobile.png"))


def test_dashboard_creates_section_folders_and_uploads_all_resource_types(browser):
    driver, base, store = browser
    wait = WebDriverWait(driver, 15)
    driver.get(f"{base}/dashboard2")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "a.edit-link"))
    driver.find_element(By.ID, "newSectionButton").click()
    driver.find_element(By.ID, "sectionName").send_keys("Servicios de prueba")
    driver.find_element(By.ID, "createSectionButton").click()
    wait.until(lambda d: d.current_url.split("#")[-1].startswith("seccion-"))
    key = driver.current_url.split("#")[-1]
    for category in ("assets", "audios", "iconos", "decoraciones"):
        assert (store.get_path().parent / "recursos" / category / key).is_dir()
    link = driver.find_element(By.CSS_SELECTOR, f'#{key} .new-route-link').get_attribute("href")
    driver.get(link)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#instructionStepList textarea"))
    image = store.get_path().parent / "nuevo.png"
    background = store.get_path().parent / "croquis.png"
    audio = store.get_path().parent / "audio.mp3"
    shutil.copyfile(DEFAULT_CONFIG.parent / "recursos/assets/Mapa/huellas sin fondo derecha.png", image)
    shutil.copyfile(DEFAULT_CONFIG.parent / "recursos/Fondos/croquis-terminal-2000x1000.png", background)
    shutil.copyfile(DEFAULT_CONFIG.parent / "recursos/audios/Mapa/AudioContaduria.mp3", audio)
    driver.find_element(By.CSS_SELECTOR, '[data-mode="assets"]').click()
    driver.find_element(By.ID, "routeAssetUploadInput").send_keys(str(image))
    wait.until(lambda d: any(asset.get("sectionId") == key for asset in store.load()["catalog"]["routeAssets"]))
    new_asset = next(asset for asset in store.load()["catalog"]["routeAssets"] if asset.get("sectionId") == key)
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, f'#segmentAssetList option[value="{new_asset["id"]}"]'))
    Select(driver.find_element(By.CSS_SELECTOR, "#segmentAssetList select")).select_by_value(new_asset["id"])
    driver.find_element(By.CSS_SELECTOR, '[data-mode="text-audio"]').click()
    replace(driver.find_element(By.ID, "routeNameInput"), "Recorrido de prueba")
    driver.find_element(By.ID, "audioUploadInput").send_keys(str(audio))
    wait.until(lambda d: d.find_element(By.ID, "routeAudioSelect").get_attribute("value").startswith(f"/recursos/audios/{key}/"))
    driver.find_element(By.ID, "saveButton").click()
    wait.until(lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado")
    route = store.load()["maps"][key]["routes"][0]
    assert route["segmentAssets"] == [new_asset["id"]]
    assert route["audio"].startswith(f"/recursos/audios/{key}/")
    driver.get(f"{base}/maps/{key}/Conf?scope=map&dashboard=2")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#backgroundSelect option"))
    driver.find_element(By.ID, "backgroundUploadInput").send_keys(str(background))
    wait.until(lambda d: d.find_element(By.ID, "editorMapImage").get_attribute("src").endswith(".png") and any(asset["name"] == "croquis" for asset in store.load()["catalog"]["backgrounds"]))
    for mode_name, input_id, select_id, category, group in (
        ("icons", "iconUploadInput", "markerAssetSelect", "iconos", "markerIcons"),
        ("decorations", "decorationUploadInput", "decorationAssetSelect", "decoraciones", "decorations"),
    ):
        driver.find_element(By.CSS_SELECTOR, f'[data-mode="{mode_name}"]').click()
        driver.find_element(By.ID, input_id).send_keys(str(image))
        wait.until(lambda d: any(asset.get("sectionId") == key for asset in store.load()["catalog"][group]))
        asset = next(asset for asset in store.load()["catalog"][group] if asset.get("sectionId") == key)
        wait.until(lambda d: d.find_element(By.ID, select_id).get_attribute("value") == asset["id"])
        assert asset["src"].startswith(f"/recursos/{category}/{key}/")
    driver.find_element(By.ID, "saveButton").click()
    wait.until(lambda d: d.find_element(By.ID, "saveStatus").text == "Guardado")
    assert store.load()["maps"][key]["background"].startswith("/recursos/Fondos/")
    driver.get(f"{base}/maps/{key}")
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "#routeControls button"))
    wait.until(lambda d: d.execute_script("return Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)"))
    assert driver.find_element(By.CSS_SELECTOR, "#routeControls button").text == "Recorrido de prueba"
    errors = [entry for entry in driver.get_log("browser") if entry["level"] == "SEVERE" and "favicon.ico" not in entry["message"]]
    assert not errors, errors


def test_dashboard_archive_restore_delete_and_direct_upload(browser):
    driver, base, store = browser
    wait = WebDriverWait(driver, 12)
    initial = store.load()
    route_id = initial["maps"]["terminal"]["routes"][0]["id"]
    driver.get(f"{base}/dashboard2")
    selector = f'#terminal tr[data-route-id="{route_id}"]'
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, selector))
    driver.find_element(By.CSS_SELECTOR, selector + ' [data-route-action="archive"]').click()
    wait.until(lambda d: d.execute_script("return document.querySelector(arguments[0])?.textContent === 'Archivada'", selector + " .status-pill"))
    assert next(route for route in store.load()["maps"]["terminal"]["routes"] if route["id"] == route_id)["archived"]
    driver.find_element(By.CSS_SELECTOR, selector + ' [data-route-action="archive"]').click()
    wait.until(lambda d: d.execute_script("return document.querySelector(arguments[0])?.textContent === 'Visible'", selector + " .status-pill"))
    driver.find_element(By.CSS_SELECTOR, selector + ' [data-route-action="delete"]').click()
    wait.until(lambda d: d.find_element(By.ID, "deleteRouteDialog").is_displayed())
    driver.find_element(By.ID, "cancelDeleteRoute").click()
    assert store.load()["maps"]["terminal"]["routes"] == initial["maps"]["terminal"]["routes"]
    driver.find_element(By.CSS_SELECTOR, selector + ' [data-route-action="delete"]').click()
    driver.find_element(By.ID, "confirmDeleteRoute").click()
    wait.until(lambda d: not d.find_elements(By.CSS_SELECTOR, selector))
    assert store.load()["catalog"] == initial["catalog"]
    assert store.load()["maps"]["mapar"] == initial["maps"]["mapar"]
    driver.find_element(By.CSS_SELECTOR, "#terminal .resource-upload-menu summary").click()
    driver.save_screenshot(str(REPORTS / "dashboard-actions-desktop.png"))
    # Selenium supplies the chosen file directly instead of operating the OS picker.
    driver.execute_script("document.getElementById('dashboardUploadInput').click = () => {}")
    driver.find_element(By.CSS_SELECTOR, '#terminal [data-upload-kind="icon"]').click()
    image = DEFAULT_CONFIG.parent / "recursos/iconos/Compartidos/Logo Muni Reu.png"
    driver.find_element(By.ID, "dashboardUploadInput").send_keys(str(image))
    wait.until(lambda d: any(asset["sectionId"] == "terminal" for asset in store.load()["catalog"]["markerIcons"]))
    wait.until(lambda d: "añadido" in d.find_element(By.ID, "dashboardNotice").text)
    assert len(store.load()["catalog"]["markerIcons"]) == len(initial["catalog"]["markerIcons"]) + 1
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True
    })
    driver.execute_script("document.getElementById('terminal').scrollIntoView({block:'start'})")
    assert driver.execute_script("return document.documentElement.scrollWidth <= innerWidth")
    driver.save_screenshot(str(REPORTS / "dashboard-actions-mobile.png"))
    for name in ("archive", "archive-restore", "trash-2", "upload"):
        assert driver.execute_script("return Array.from(document.images).filter(img => img.src.endsWith(arguments[0]+'.svg')).every(img => img.complete && img.naturalWidth > 0)", name)
