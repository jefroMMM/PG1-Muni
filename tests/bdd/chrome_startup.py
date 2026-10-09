"""Diagnóstico de Chrome en CI; no abre la aplicación ni usa perfiles del usuario."""
import json
import os
import subprocess
import tempfile
from pathlib import Path


def probe(binary, no_sandbox=False):
    with tempfile.TemporaryDirectory(prefix="bdd-chrome-probe-") as profile:
        command = [binary, "--headless=new", "--no-first-run", "--no-default-browser-check",
                   f"--user-data-dir={profile}", "--dump-dom"]
        if no_sandbox:
            command.append("--no-sandbox")
        command.append("data:text/html,<title>BDD startup probe</title>")
        try:
            result = subprocess.run(command, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=15)
            return {"no_sandbox": no_sandbox, "exit_code": result.returncode,
                    "ready": result.returncode == 0 and "BDD startup probe" in result.stdout,
                    "stderr": result.stderr[-12000:]}
        except subprocess.TimeoutExpired:
            return {"no_sandbox": no_sandbox, "ready": False, "error": "Chrome no terminó el diagnóstico en 15 segundos."}


def main():
    reports = Path(__file__).parent / "reports"
    reports.mkdir(exist_ok=True)
    binary = os.environ["BDD_CHROME_BINARY"]
    first = probe(binary)
    attempts = [first]
    sandbox_errors = ("No usable sandbox", "Running as root without --no-sandbox",
                      "Failed to move to new namespace")
    no_sandbox = False
    if not first["ready"] and any(message in first.get("stderr", "") for message in sandbox_errors):
        # Solo el navegador de pruebas del runner efímero; nunca la aplicación.
        no_sandbox = True
        attempts.append(probe(binary, no_sandbox=True))
    payload = {"ready": attempts[-1]["ready"], "no_sandbox": no_sandbox, "attempts": attempts}
    (reports / "chrome-startup.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"no-sandbox={int(no_sandbox)}\n")
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
