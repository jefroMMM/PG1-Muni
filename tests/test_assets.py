"""Active configuration and ES module references must resolve inside the app."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from strings(nested)


class AssetTests(unittest.TestCase):
    def test_configured_images_audio_and_uploads_exist(self):
        for name in ("routes-config.json", "routes-config.default.json"):
            config = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
            for url in set(strings(config)):
                if not url.startswith(("/assets/", "/MapaR/", "/uploads/", "/recursos/")):
                    continue
                path = unquote(urlsplit(url).path)
                target = ROOT / "data" / path.lstrip("/") if path.startswith(("/uploads/", "/recursos/")) else FRONTEND / path.lstrip("/")
                with self.subTest(config=name, url=url):
                    self.assertTrue(target.is_file(), target)

    def test_module_imports_exist_and_do_not_depend_on_archives(self):
        for source in (FRONTEND / "assets/js").rglob("*.js"):
            code = source.read_text(encoding="utf-8")
            for dependency in re.findall(r'from\s+[\"\x27]([^\"\x27]+)[\"\x27]', code):
                with self.subTest(source=source.name, dependency=dependency):
                    self.assertTrue(dependency.startswith("."))
                    target = (source.parent / dependency).resolve()
                    self.assertTrue(target.is_relative_to(FRONTEND.resolve()))
                    self.assertTrue(target.is_file())

    def test_local_stylesheets_and_entry_scripts_exist(self):
        for page in FRONTEND.rglob("*.html"):
            code = page.read_text(encoding="utf-8")
            for url in re.findall(r'(?:src|href)="(/assets/[^"?#]+\.(?:js|css))"', code):
                with self.subTest(page=page.name, url=url):
                    self.assertTrue((FRONTEND / url.lstrip("/")).is_file())


if __name__ == "__main__":
    unittest.main()
