"""Dashboard actions update only their route and retain shared resources."""
import copy
import tempfile
import unittest
from pathlib import Path

from backend.app import DEFAULT_CONFIG, create_app
from backend.storage import ConfigStore


class RouteActionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = ConfigStore(lambda: self.root / "config.json", lambda: DEFAULT_CONFIG)
        self.client = create_app(self.store, self.root / "uploads").test_client()
        self.initial = self.store.load()
        self.route = self.initial["maps"]["terminal"]["routes"][0]
        self.url = f"/api/maps/terminal/routes/{self.route['id']}"

    def tearDown(self):
        self.temp.cleanup()

    def test_archive_and_restore_preserve_route_details_and_other_maps(self):
        data = self.store.load()
        data["maps"]["terminal"]["routes"][0]["name"] = "Cambio en otra ventana"
        self.store.save(data)
        for archived in (True, False):
            response = self.client.patch(self.url + "/status", json={"archived": archived, "name": "No debe sobrescribir"})
            self.assertEqual(response.status_code, 200)
            expected = copy.deepcopy(data)
            expected["maps"]["terminal"]["routes"][0]["archived"] = archived
            self.assertEqual(self.store.load(), expected)

    def test_delete_removes_only_the_selected_route(self):
        self.assertEqual(self.client.delete(self.url).status_code, 200)
        expected = copy.deepcopy(self.initial)
        expected["maps"]["terminal"]["routes"] = expected["maps"]["terminal"]["routes"][1:]
        self.assertEqual(self.store.load(), expected)
        self.assertEqual(self.client.delete(self.url).status_code, 404)

    def test_last_route_can_be_deleted(self):
        config = self.store.load()
        config["maps"]["terminal"]["routes"] = [self.route]
        self.store.save(config)
        self.assertEqual(self.client.delete(self.url).status_code, 200)
        self.assertEqual(self.store.load()["maps"]["terminal"]["routes"], [])
        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)

    def test_invalid_status_and_unknown_targets_do_not_modify_data(self):
        for value in (None, "true", 1, [], {}):
            self.assertEqual(self.client.patch(self.url + "/status", json={"archived": value}).status_code, 400)
        for url in ("/api/maps/missing/routes/test", "/api/maps/terminal/routes/missing"):
            self.assertEqual(self.client.patch(url + "/status", json={"archived": True}).status_code, 404)
            self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(self.store.load(), self.initial)


if __name__ == "__main__":
    unittest.main()
