"""Scoped saves must preserve changes made in other editor windows."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from backend import app as backend


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_path = backend.CONFIG_PATH
        backend.CONFIG_PATH = Path(self.temp.name) / "routes-config.json"
        self.initial = json.loads(backend.DEFAULT_CONFIG.read_text(encoding="utf-8"))
        backend.save_config(self.initial)
        self.client = backend.app.test_client()

    def tearDown(self):
        backend.CONFIG_PATH = self.previous_path
        self.temp.cleanup()

    def save_route(self, route, **extra):
        return self.client.patch(f"/api/maps/terminal/routes/{route['id']}", json={"route": route, **extra})

    def test_dashboard_and_editor_pages(self):
        for url in ("/dashboard", "/dashboard/", "/dashboard2", "/preview", "/Conf?scope=route&route=contaduria", "/MapaR/Conf?scope=map", "/assets/js/dashboard.js", "/assets/css/dashboard.css"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_two_route_windows_preserve_each_others_changes(self):
        routes = copy.deepcopy(self.initial["maps"]["terminal"]["routes"])
        routes[0]["name"] = "Contaduria editada"
        routes[1]["instructions"] = "Indicaciones de otra ventana"
        self.assertEqual(self.save_route(routes[0]).status_code, 200)
        self.assertEqual(self.save_route(routes[1]).status_code, 200)
        saved = backend.load_config()
        self.assertEqual(saved["maps"]["terminal"]["routes"][0]["name"], routes[0]["name"])
        self.assertEqual(saved["maps"]["terminal"]["routes"][1]["instructions"], routes[1]["instructions"])
        self.assertEqual(saved["maps"]["mapar"], self.initial["maps"]["mapar"])

    def test_route_save_cannot_change_map_image(self):
        route = copy.deepcopy(self.initial["maps"]["terminal"]["routes"][0])
        route["background"] = "/bad.png"
        self.assertEqual(self.save_route(route, map={"background": "/bad.png"}).status_code, 200)
        saved = backend.load_config()["maps"]["terminal"]
        self.assertEqual(saved["background"], self.initial["maps"]["terminal"]["background"])
        self.assertNotIn("background", saved["routes"][0])

    def test_map_save_preserves_route_changes_from_another_window(self):
        route = copy.deepcopy(self.initial["maps"]["terminal"]["routes"][0])
        route["instructions"] = "Pasos nuevos"
        self.assertEqual(self.save_route(route).status_code, 200)
        response = self.client.patch("/api/maps/terminal", json={"map": {
            "background": "/uploads/mapas/new.png", "routes": []
        }})
        self.assertEqual(response.status_code, 200)
        saved = backend.load_config()["maps"]["terminal"]
        self.assertEqual(saved["background"], "/uploads/mapas/new.png")
        self.assertEqual(saved["routes"][0]["instructions"], "Pasos nuevos")
        self.assertEqual(len(saved["routes"]), 5)

    def test_uploaded_assets_from_two_windows_are_retained(self):
        routes = copy.deepcopy(self.initial["maps"]["terminal"]["routes"])
        for index in (0, 1):
            catalog = copy.deepcopy(self.initial["catalog"])
            catalog["audios"].append({"id": f"new-{index}", "name": "Nuevo audio", "src": f"/uploads/audios/{index}.mp3"})
            self.assertEqual(self.save_route(routes[index], catalog=catalog).status_code, 200)
        ids = {audio["id"] for audio in backend.load_config()["catalog"]["audios"]}
        self.assertTrue({"new-0", "new-1"}.issubset(ids))

    def test_invalid_or_missing_routes_do_not_change_config(self):
        route = copy.deepcopy(self.initial["maps"]["terminal"]["routes"][0])
        for change in ({"name": " "}, {"nodes": []}, {"nodes": [{"x": -1, "y": 0}, {"x": 2, "y": 3}]}):
            with self.subTest(change=change):
                self.assertEqual(self.save_route({**route, **change}).status_code, 400)
                self.assertEqual(backend.load_config(), self.initial)
        missing = {**route, "id": "missing"}
        self.assertEqual(self.save_route(missing).status_code, 404)

    def test_new_section_starts_empty_and_keeps_existing_maps(self):
        response = self.client.post("/api/maps", json={"name": "Servicios municipales", "icon": "briefcase", "template": "mapar"})
        self.assertEqual(response.status_code, 201)
        key = response.get_json()["mapKey"]
        saved = backend.load_config()
        section = saved["maps"][key]
        self.assertEqual(section["sectionName"], "Servicios municipales")
        self.assertEqual(section["sectionIcon"], "briefcase")
        self.assertEqual(section["routes"], [])
        self.assertEqual(section["markers"], [])
        self.assertEqual(section["background"], self.initial["maps"]["mapar"]["background"])
        for map_key in ("terminal", "mapar"):
            self.assertEqual(saved["maps"][map_key], self.initial["maps"][map_key])
        for url in (f"/maps/{key}", f"/maps/{key}/Conf"):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_new_route_is_added_only_to_its_section_and_duplicate_is_rejected(self):
        response = self.client.post("/api/maps", json={"name": "Nueva sección", "icon": "pin", "template": "terminal"})
        key = response.get_json()["mapKey"]
        route = copy.deepcopy(self.initial["maps"]["terminal"]["routes"][0])
        route.update({"id": "new-route", "name": "Atención al vecino"})
        response = self.client.post(f"/api/maps/{key}/routes", json={"route": route})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(backend.load_config()["maps"][key]["routes"]), 1)
        self.assertEqual(backend.load_config()["maps"]["terminal"], self.initial["maps"]["terminal"])
        self.assertEqual(self.client.post(f"/api/maps/{key}/routes", json={"route": route}).status_code, 409)
        route["instructions"] = "Pasos nuevos"
        self.assertEqual(self.client.patch(f"/api/maps/{key}/routes/new-route", json={"route": route}).status_code, 200)
        self.assertEqual(backend.load_config()["maps"][key]["routes"][0]["instructions"], "Pasos nuevos")

    def test_invalid_section_and_route_creation_preserve_config(self):
        for payload in ({"name": " "}, {"name": "Test", "icon": "unknown"}, {"name": "Test", "template": "unknown"}, {"name": "Test", "icon": []}):
            self.assertEqual(self.client.post("/api/maps", json=payload).status_code, 400)
            self.assertEqual(backend.load_config(), self.initial)
        self.assertEqual(self.client.post("/api/maps/terminal/routes", json={"route": {"id": "new", "name": "Test", "nodes": []}}).status_code, 400)
        self.assertEqual(backend.load_config(), self.initial)
        self.assertEqual(self.client.get("/maps/unknown/Conf").status_code, 404)

    def test_preview_page_does_not_save_anything(self):
        self.assertEqual(self.client.get("/preview").status_code, 200)
        self.assertEqual(backend.load_config(), self.initial)


if __name__ == "__main__":
    unittest.main()
