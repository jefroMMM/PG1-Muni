"""Abre las cuatro interfaces anteriores en ventanas de escritorio independientes."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request

import webview


BASE_URL = "http://localhost:8080"
ROUTES = ("1", "2", "3", "4")


def server_is_available() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/config", timeout=2):
            return True
    except urllib.error.URLError:
        return False


def open_windows() -> None:
    for route in ROUTES:
        webview.create_window(
            title=f"Terminal Municipal · Ruta {route}",
            url=f"{BASE_URL}/{route}",
            maximized=True,
            min_size=(900, 600),
        )

    webview.start(gui="edgechromium", private_mode=True)


if __name__ == "__main__":
    if not server_is_available():
        sys.exit("No se puede conectar a localhost:8080. Ejecuta primero: docker compose up -d")
    open_windows()
