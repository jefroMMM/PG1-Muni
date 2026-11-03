import { initRouteViewer } from "./shared/route-viewer.js";
import { getMapKey } from "./shared/sections.js";

initRouteViewer(getMapKey()).catch((error) => {
  const message = document.createElement("main");
  message.className = "terminal-error";
  message.textContent = error.message;
  document.body.replaceChildren(message);
});
