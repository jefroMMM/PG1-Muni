"""Persistence and application isolation without touching the working data."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.app import DEFAULT_CONFIG, create_app
from backend.storage import ConfigStore


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "routes-config.json"
        self.store = ConfigStore(lambda: self.path, lambda: DEFAULT_CONFIG)
        self.client = create_app(self.store, Path(self.temp.name) / "uploads").test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_cached_reads_are_independent_snapshots(self):
        data = self.store.load()
        original = data["maps"]["terminal"]["title"]
        data["maps"]["terminal"]["title"] = "Not saved"
        self.assertEqual(self.store.load()["maps"]["terminal"]["title"], original)

    def test_external_replacement_invalidates_cache(self):
        data = self.store.load()
        data["maps"]["terminal"]["title"] = "External replacement"
        replacement = self.path.with_suffix(".new")
        replacement.write_text(json.dumps(data), encoding="utf-8")
        replacement.replace(self.path)
        self.assertEqual(self.store.load()["maps"]["terminal"]["title"], "External replacement")

    def test_failed_serialization_preserves_original_and_removes_temporary_file(self):
        original = self.store.load()
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.store.save({"bad": float("nan")})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.store.load(), original)
        self.assertEqual([file.name for file in self.path.parent.iterdir()], [self.path.name])

    def test_invalid_complete_config_does_not_replace_existing_data(self):
        original = self.store.load()
        invalid = json.loads(json.dumps(original))
        invalid["maps"]["terminal"]["routes"][0]["nodes"] = []
        self.assertEqual(self.client.put("/api/config", json=invalid).status_code, 400)
        self.assertEqual(self.store.load(), original)
        self.assertEqual(self.client.put("/api/config", json=original).status_code, 200)

    def test_bad_catalog_items_return_validation_error(self):
        data = self.store.load()
        route = data["maps"]["terminal"]["routes"][0]
        response = self.client.patch(f"/api/maps/terminal/routes/{route['id']}", json={
            "route": route, "catalog": {"routeAssets": ["not an asset"]}
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.store.load(), data)

    def test_archived_files_are_not_public(self):
        for path in ("/descartados/README.md", "/Clasmorfismo/index.html", "/fork-core/route-app.js"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


if __name__ == "__main__":
    unittest.main()
