import { initRouteViewer } from "./shared/route-viewer.js";

initRouteViewer("terminal").catch((error) => {
  document.body.innerHTML = `<main class="terminal-error">${error.message}</main>`;
});
