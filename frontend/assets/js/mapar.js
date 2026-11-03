import { initRouteViewer } from "./shared/route-viewer.js";

initRouteViewer("mapar").catch((error) => {
  const message = document.createElement("main");
  message.className = "terminal-error";
  message.textContent = error.message;
  document.body.replaceChildren(message);
});
