import { initRouteViewer } from "./shared/route-viewer.js";

const sectionKey = window.location.pathname.match(/^\/maps\/([^/]+)/)?.[1];
initRouteViewer(sectionKey ? decodeURIComponent(sectionKey) : "terminal").catch((error) => {
  document.body.innerHTML = `<main class="terminal-error">${error.message}</main>`;
});
