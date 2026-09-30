import { initRouteViewer } from "./shared/route-viewer.js";

let initialized = false;
window.addEventListener("message", async (event) => {
  if (event.origin !== window.location.origin || event.source !== window.parent || event.data?.type !== "route-preview-data" || initialized) return;
  initialized = true;
  const { config, mapKey, routeId } = event.data;
  try {
    if (mapKey === "mapar" || config.maps[mapKey].routeStyle === "assets-only") {
      document.querySelector(".terminal").classList.add("mapr-terminal");
      document.querySelector(".main-area").classList.add("mapr-main");
      document.querySelector(".map-frame").classList.add("mapr-frame");
      document.querySelector(".welcome-panel").classList.add("mapr-panel");
      document.getElementById("routeControls").classList.add("mapr-controls");
    }
    await initRouteViewer(mapKey, { config, routeId });
  } catch (error) { document.getElementById("panelContent").textContent = error.message; }
});
if (window.parent !== window) window.parent.postMessage({ type: "route-preview-ready" }, window.location.origin);
else document.getElementById("panelContent").textContent = "Abre la previsualización desde el editor de una ruta.";
