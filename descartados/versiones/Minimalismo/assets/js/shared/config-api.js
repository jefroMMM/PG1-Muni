export async function loadRouteConfig() {
  const response = await fetch("/api/config", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("No se pudo cargar la configuracion");
  }
  return response.json();
}

export async function saveRouteConfig(config) {
  const response = await fetch("/api/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "No se pudo guardar la configuracion");
  }

  return response.json();
}
