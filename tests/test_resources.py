"""Section resource ownership, uploads, migration and compatibility."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.app import DEFAULT_CONFIG, create_app
from backend.resources import GROUPS, ResourceLibrary
from backend.storage import ConfigStore
from tools.migrate_resources import migrate


class ResourceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = ConfigStore(lambda: self.root / "config.json", lambda: DEFAULT_CONFIG)
        self.client = create_app(self.store, self.root / "uploads").test_client()
        self.resources = ResourceLibrary(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def upload(self, kind, key="terminal", filename="sample.png"):
        return self.client.post("/api/upload", data={
            "kind": kind, "mapKey": key, "file": (io.BytesIO(b"resource bytes"), filename)
        }, content_type="multipart/form-data")

    def test_new_section_creates_all_its_own_directories(self):
        response = self.client.post("/api/maps", json={"name": "Servicios", "template": "terminal"})
        self.assertEqual(response.status_code, 201)
        key = response.get_json()["mapKey"]
        for category in ("assets", "audios", "iconos", "decoraciones"):
            self.assertTrue((self.resources.root / category / key).is_dir())
        self.assertTrue((self.resources.root / "Fondos").is_dir())
        config = self.store.load()
        config["maps"][key]["sectionName"] = "Otro nombre"
        self.store.save(config)
        self.assertEqual(self.store.load()["maps"][key]["resourceFolder"], key)

    def test_uploads_are_owned_by_their_section_and_persist_without_editor_save(self):
        for kind, group, category, filename in (
            ("route-asset", "routeAssets", "assets", "walk.png"),
            ("audio", "audios", "audios", "guide.mp3"),
            ("icon", "markerIcons", "iconos", "marker.png"),
            ("decoration", "decorations", "decoraciones", "tree.png"),
            ("map", "backgrounds", "Fondos", "background.png"),
        ):
            with self.subTest(kind=kind):
                response = self.upload(kind, "mapar", filename)
                self.assertEqual(response.status_code, 201)
                asset = response.get_json()
                self.assertEqual(asset["sectionId"], "shared" if kind == "map" else "mapar")
                self.assertTrue(asset["src"].startswith(f"/recursos/{category}/" + ("" if kind == "map" else "MapaR/")))
                self.assertIn(asset, self.store.load()["catalog"][group])
                with self.client.get(asset["src"]) as result:
                    self.assertEqual(result.status_code, 200)
                    self.assertEqual(result.data, b"resource bytes")

    def test_invalid_uploads_do_not_write_files_or_change_configuration(self):
        original = self.store.load()
        for kind, key, filename in (("unknown", "terminal", "x.png"), ("icon", "missing", "x.png"), ("icon", "../../outside", "x.png"), ("audio", "terminal", "x.exe")):
            with self.subTest(kind=kind, key=key):
                self.assertEqual(self.upload(kind, key, filename).status_code, 400)
                self.assertEqual(self.store.load(), original)
        self.assertFalse(self.resources.root.exists())

    def test_stale_full_save_preserves_new_uploads_and_ownership(self):
        stale = self.store.load()
        asset = self.upload("route-asset", "mapar").get_json()
        self.assertEqual(self.client.put("/api/config", json=stale).status_code, 200)
        saved = next(item for item in self.store.load()["catalog"]["routeAssets"] if item["id"] == asset["id"])
        self.assertEqual(saved, asset)

    def test_resource_delivery_rejects_traversal_and_metadata_files(self):
        for path in ("/recursos/../config.json", "/recursos/assets/Mapa/.gitkeep", "/recursos/assets/Mapa/../../../../config.json", "/recursos/unknown/x.png"):
            self.assertEqual(self.client.get(path).status_code, 404)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        route = {"id": "office", "name": "Office", "archived": False,
                 "nodes": [{"x": 10, "y": 10}, {"x": 100, "y": 100}], "segmentAssets": ["walk"],
                 "audio": "/assets/Audios/guide.mp3", "instructions": "Keep going", "durationSeconds": 30}
        self.config = {"catalog": {
            "backgrounds": [{"id": "floor", "src": "/assets/images/floor.png"}, {"id": "city", "src": "/MapaR/images/city.png"}],
            "routeAssets": [{"id": "walk", "type": "single", "src": "/assets/images/walk.png"}, {"id": "taxi", "type": "single", "src": "/MapaR/images/taxi.png"}],
            "audios": [{"id": "guide", "src": route["audio"]}],
            "markerIcons": [{"id": "muni-logo", "src": "/assets/images/logo.png"}], "decorations": []},
            "maps": {"terminal": {"background": "/assets/images/floor.png", "logo": "/assets/images/logo.png", "routes": [route]},
                     "mapar": {"background": "/MapaR/images/city.png", "logo": "/assets/images/logo.png", "routes": []}}}
        for path in ("assets/images/floor.png", "MapaR/images/city.png", "assets/images/walk.png", "MapaR/images/taxi.png", "assets/Audios/guide.mp3", "assets/images/logo.png"):
            target = self.root / "frontend" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.encode())
        for name in ("routes-config.json", "routes-config.default.json"):
            (self.data / name).write_text(json.dumps(self.config), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_does_not_modify_any_file(self):
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = migrate(self.root)
        self.assertEqual(result["configs"], 2)
        self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_migration_preserves_content_routes_backups_and_is_idempotent(self):
        result = migrate(self.root, apply=True)
        self.assertEqual(result["configs"], 2)
        migrated = json.loads((self.data / "routes-config.json").read_text())
        self.assertEqual(migrated["catalog"]["routeAssets"][0]["sectionId"], "terminal")
        self.assertEqual(migrated["catalog"]["routeAssets"][1]["sectionId"], "mapar")
        self.assertEqual(migrated["maps"]["terminal"]["logo"], "/recursos/iconos/Compartidos/logo.png")
        old_route = self.config["maps"]["terminal"]["routes"][0]
        new_route = migrated["maps"]["terminal"]["routes"][0]
        self.assertEqual({key: value for key, value in old_route.items() if key != "audio"}, {key: value for key, value in new_route.items() if key != "audio"})
        self.assertEqual((self.data / "recursos/assets/Mapa/walk.png").read_bytes(), b"assets/images/walk.png")
        self.assertEqual(json.loads((Path(result["backup"]) / "routes-config.json").read_text()), self.config)
        self.assertEqual(migrate(self.root, apply=True)["configs"], 0)

    def test_missing_source_prevents_partial_migration(self):
        (self.root / "frontend/assets/images/walk.png").unlink()
        before = (self.data / "routes-config.json").read_bytes()
        with self.assertRaises(ValueError):
            migrate(self.root, apply=True)
        self.assertEqual((self.data / "routes-config.json").read_bytes(), before)
        self.assertFalse((self.data / "recursos").exists())

    def test_legacy_urls_redirect_and_stale_payloads_are_canonicalized(self):
        migrate(self.root, apply=True)
        path = self.data / "routes-config.json"
        store = ConfigStore(lambda: path, lambda: self.data / "routes-config.default.json")
        client = create_app(store).test_client()
        response = client.get("/assets/images/walk.png")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/recursos/assets/Mapa/walk.png"))
        with client.get(response.location) as media:
            self.assertEqual(media.status_code, 200)
        stale = copy.deepcopy(self.config["maps"]["terminal"]["routes"][0])
        response = client.patch("/api/maps/terminal/routes/office", json={"route": stale})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(store.load()["maps"]["terminal"]["routes"][0]["audio"].startswith("/recursos/audios/Mapa/"))


if __name__ == "__main__":
    unittest.main()
