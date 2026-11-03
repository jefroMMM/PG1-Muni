async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.error || `No se pudo completar la solicitud (${response.status})`);
  }
  if (result === null) throw new Error("El servidor no devolvio una respuesta valida");
  return result;
}

function sendJson(url, method, payload) {
  return requestJson(url, {
    method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
  });
}

export function loadRouteConfig() {
  return requestJson("/api/config", { cache: "no-store" });
}

export function saveRouteConfig(config) {
  return sendJson("/api/config", "PUT", config);
}

export function createMap(payload) {
  return sendJson("/api/maps", "POST", payload);
}

export function setRouteArchived(mapKey, routeId, archived) {
  return sendJson(`/api/maps/${encodeURIComponent(mapKey)}/routes/${encodeURIComponent(routeId)}/status`, "PATCH", { archived });
}

export function deleteRoute(mapKey, routeId) {
  return requestJson(`/api/maps/${encodeURIComponent(mapKey)}/routes/${encodeURIComponent(routeId)}`, { method: "DELETE" });
}

export function uploadFile(file, kind, mapKey) {
  const body = new FormData();
  body.append("file", file);
  body.append("kind", kind);
  body.append("mapKey", mapKey);
  return requestJson("/api/upload", { method: "POST", body });
}

export function saveEditorScope(mapKey, routeId, payload, create = false) {
  const endpoint = routeId
    ? `/api/maps/${encodeURIComponent(mapKey)}/routes${create ? "" : `/${encodeURIComponent(routeId)}`}`
    : `/api/maps/${encodeURIComponent(mapKey)}`;
  return sendJson(endpoint, create ? "POST" : "PATCH", payload);
}
