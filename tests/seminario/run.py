"""Ejecuta Cypress contra Flask real con almacenamiento temporal y verifica integridad.

Uso desde la raíz: python tests/seminario/run.py
No modifica código de producción, no utiliza Docker y no necesita el antiguo BDD.
"""



import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen



ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))



from backend.app import DEFAULT_CONFIG, create_app
from backend.storage import ConfigStore
from werkzeug.serving import make_server





def protected_snapshot(audio):
    """Incluye archivos y directorios para detectar cambios o nuevas cargas reales."""
    entries = list((ROOT / "data").rglob("*")) + [audio, HERE / "fixtures/croquis.png"]
    return {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):
            hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "directory"
            for p in entries}


def main():

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aporte", choices=["todos", "e2e", "api"], default="todos")
    parser.add_argument("--defecto-controlado", action="store_true",
                        help="Demuestra que las pruebas detectan un defecto SOLO en esta instancia temporal")
    args = parser.parse_args()


    audio = Path(os.environ.get("SEMINARIO_AUDIO", ROOT / "Audio de prueba.mp3")).resolve()


    if not audio.is_file():
        parser.error("Falta Audio de prueba.mp3 en la raíz o la ruta SEMINARIO_AUDIO")
    if not (HERE / "node_modules/.bin/cypress.cmd").exists() and not (HERE / "node_modules/.bin/cypress").exists():
        parser.error("Primero ejecuta npm ci en tests/seminario")


    label = "defecto-controlado" if args.defecto_controlado else "normal"
    stamp = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y%m%d-%H%M%S-%f")
    output = HERE / "results" / f"{stamp}-{label}"
    output.mkdir(parents=True)

    before = protected_snapshot(audio)


    code = 1


    with tempfile.TemporaryDirectory(prefix="seminario-muni-") as temporary:
        folder = Path(temporary)
        config = folder / "routes-config.json"

        store = ConfigStore(lambda: config, lambda: DEFAULT_CONFIG)
        seed = store.load()

        baseline = folder / "baseline.json"
        baseline.write_text(json.dumps(seed), encoding="utf-8")


        application = create_app(store, folder / "uploads")
        application.config["TESTING"] = True



        if args.defecto_controlado:
            from backend import api
            original_validation = api.valid_route



            def weakened_validation(route, route_id):
                candidate = dict(route) if isinstance(route, dict) else route
                if isinstance(candidate, dict) and isinstance(candidate.get("name"), str) and not candidate["name"].strip():
                    candidate["name"] = "Nombre aceptado por defecto controlado"
                return original_validation(candidate, route_id)
            api.valid_route = weakened_validation


        server = make_server("127.0.0.1", 0, application, threaded=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"


        environment = os.environ.copy()
        environment.update(SEMINARIO_CONFIG=str(config), SEMINARIO_BASELINE=str(baseline),
                           SEMINARIO_RESULTS=str(output), SEMINARIO_AUDIO=str(audio),
                           CYPRESS_BASE_URL=base_url, CYPRESS_NO_COMMAND_LOG="1")

        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        command = [npm, "run", "cypress:run", "--", "--browser",
                   os.environ.get("SEMINARIO_BROWSER", "chrome")]

        if args.aporte != "todos":
            command += ["--spec", f"{args.aporte}.cy.js"]
        try:


            with urlopen(base_url + "/api/config", timeout=5) as response:
                assert response.status == 200

            with (output / "cypress.log").open("w", encoding="utf-8") as log:

                process = subprocess.Popen(command, cwd=HERE, env=environment,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding="utf-8", errors="replace")
                try:
                    for line in process.stdout:
                        print(line, end="", flush=True)
                        log.write(line)
                    code = process.wait()
                finally:

                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=15)
        finally:


            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


            after = protected_snapshot(audio)
            integrity = {"unchanged": before == after, "before": before, "after": after}
            (output / "integridad.json").write_text(json.dumps(integrity, indent=2), encoding="utf-8")


            metadata = {"date_guatemala": stamp, "base_url": base_url,
                        "isolated_server_stopped": not thread.is_alive(), "python": sys.version,
                        "aporte": args.aporte, "controlled_defect": args.defecto_controlado,
                        "cypress_exit_code": code, "original_data_unchanged": before == after}
            (output / "ejecucion.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


            if before != after or thread.is_alive():
                code = 1
    print(f"\nEvidencias: {output}\nDatos originales intactos: {before == after}")
    return code



if __name__ == "__main__":
    raise SystemExit(main())
