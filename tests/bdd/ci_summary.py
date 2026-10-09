"""Resume una ejecución de CI sin confundir datos antiguos con pruebas aprobadas."""
import argparse
import json
import os
from pathlib import Path


def summarize(reports, step_outcome):
    expected = {f"BDD{i:02}" for i in range(1, 11)}
    result = None
    problem = ""
    try:
        result = json.loads((reports / "resultados.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        problem = f"No se pudo leer el reporte generado: {type(error).__name__}."

    if step_outcome != "success":
        problem = ("Pytest falló; consulta el log y las causas de los escenarios." if step_outcome == "failure"
                   else "Las pruebas no terminaron correctamente; revisa la preparación y los pasos anteriores.")
    elif result is not None:
        scenarios = result.get("scenarios", [])
        if len(scenarios) != 10 or {s.get("id") for s in scenarios} != expected:
            problem = "El reporte no contiene exactamente los diez escenarios originales."
        elif any(s.get("outcome") != "aprobado" for s in scenarios) or result.get("exit_status") != 0:
            problem = "Hay escenarios fallidos, omitidos o no ejecutados, o pytest devolvió un error."
        elif result.get("environment", {}).get("real_data_unchanged") is not True:
            problem = "La comprobación de integridad de los archivos no fue satisfactoria."
        elif not (reports / "junit.xml").is_file():
            problem = "No se generó el reporte JUnit requerido."

    approved = not problem and result is not None
    status = {"approved": approved, "pytest_step_outcome": step_outcome,
              "expected_scenarios": 10, "totals": result.get("totals", {}) if result else {},
              "cause": problem, "github_execution": bool(os.environ.get("GITHUB_ACTIONS"))}
    lines = ["# Laboratorio BDD — resultado de CI", "",
             "**APROBADO: los 10 escenarios pasaron y los archivos protegidos siguen intactos.**" if approved
             else "**FALLIDO O INCOMPLETO: no se confirmó la aprobación de los 10 escenarios.**", ""]
    if problem:
        lines += [problem, ""]
    if not status["github_execution"]:
        lines += ["Validación local del resumen: no acredita una ejecución en GitHub Actions.", ""]
    if result:
        totals = result.get("totals", {})
        lines += [f"Aprobados: {totals.get('aprobado', 0)} · Fallidos: {totals.get('fallido', 0)} · "
                  f"Omitidos: {totals.get('omitido', 0)} · No ejecutados: {totals.get('no ejecutado', 0)}.", ""]
    lines += ["Consulta el artifact `bdd-reportes-<run_id>-<intento>` para descargar los reportes disponibles.",
              "Si falla la preparación, puede no existir JUnit: no se fabrican resultados de pruebas.", ""]
    return status, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, default=Path(__file__).parent / "reports")
    args = parser.parse_args()
    args.reports.mkdir(parents=True, exist_ok=True)
    status, markdown = summarize(args.reports, os.environ.get("BDD_STEP_OUTCOME", "unknown"))
    (args.reports / "workflow-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.reports / "ci-summary.md").write_text(markdown, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
            output.write(markdown)
    print(markdown)
    return 0 if status["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
