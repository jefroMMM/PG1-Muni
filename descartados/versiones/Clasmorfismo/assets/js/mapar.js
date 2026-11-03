import { initRouteViewer } from "./shared/route-viewer.js";

initRouteViewer("mapar").catch((error) => {
  document.body.innerHTML = `<main class="terminal-error">${error.message}</main>`;
});
