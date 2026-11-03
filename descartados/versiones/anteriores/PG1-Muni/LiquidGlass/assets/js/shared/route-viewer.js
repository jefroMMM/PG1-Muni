import { loadRouteConfig } from "./config-api.js";
import {
  createSvgElement,
  renderDecorations,
  renderFootprints,
  renderMapMarkers,
  routePathFromNodes
} from "./map-utils.js";

export async function initRouteViewer(mapKey) {
  const config = await loadRouteConfig();
  const mapConfig = config.maps[mapKey];
  const catalog = config.catalog;

  const mapImage = document.getElementById("mapImage");
  const routeLayer = document.getElementById("routeLayer");
  const routePath = document.getElementById("routePath");
  const routeFootprints = document.getElementById("routeFootprints");
  const markerLayer = document.getElementById("markerLayer");
  const decorationLayer = document.getElementById("decorationLayer");
  const highlightLayer = document.getElementById("highlightLayer");
  const controls = document.getElementById("routeControls");
  const panelLogo = document.getElementById("panelLogo");
  const panelContent = document.getElementById("panelContent");
  const terminal = document.querySelector(".terminal");

  let activeAudio = null;
  let exitTimer = null;
  let resetTimer = null;

  document.title = mapConfig.title;
  mapImage.src = mapConfig.background;
  panelLogo.src = mapConfig.logo;
  routeLayer.setAttribute("viewBox", mapConfig.viewBox);

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function getInstructionSteps(instructions = "") {
    const cleaned = instructions
      .replace(/\r/g, "\n")
      .split(/\n+|(?<=\.)\s+|(?<=;)\s+/)
      .map((step) => step.replace(/^\s*\d+[\).\-\s]+/, "").trim())
      .map((step) => step.replace(/\.$/, ""))
      .filter(Boolean);

    return cleaned.length ? cleaned : ["Ruta sin indicaciones escritas"];
  }

  function stopAudio() {
    if (!activeAudio) {
      return;
    }

    activeAudio.pause();
    activeAudio.currentTime = 0;
    activeAudio = null;
  }

  function showDefaultPanel() {
    const content = mapConfig.defaultPanel;
    terminal?.classList.remove("route-active");
    panelContent.className = "welcome-content";
    panelContent.innerHTML = `
      <p class="welcome-kicker">${content.kicker}</p>
      <h1>${content.title}</h1>
      <p>${content.text}</p>
      ${content.hint ? `<span>${content.hint}</span>` : ""}
    `;
  }

  function showRoutePanel(route) {
    const steps = getInstructionSteps(route.instructions);
    const density = steps.length >= 8 ? "dense" : steps.length >= 5 ? "compact" : "normal";
    terminal?.classList.add("route-active");
    panelContent.className = `welcome-content route-content route-steps-${density}`;
    panelContent.innerHTML = `
      <p class="welcome-kicker">Indicaciones</p>
      <h1>${escapeHtml(route.name)}</h1>
      <ol class="route-instruction-list">
        ${steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}
      </ol>
    `;
  }

  function renderHighlights(activeRouteId = "") {
    const polygons = mapConfig.routes
      .filter((route) => route.highlightPolygon)
      .map((route) => createSvgElement("polygon", {
        class: `office-highlight ${route.id === activeRouteId ? "active" : ""}`,
        points: route.highlightPolygon,
        "data-route-id": route.id
      }));

    highlightLayer.replaceChildren(...polygons);
  }

  function clearRouteDisplay() {
    routePath.removeAttribute("d");
    routePath.style.transition = "none";
    routePath.style.strokeDashoffset = "0";
    routePath.classList.remove("leaving");
    routeFootprints.replaceChildren();
    renderHighlights();
    controls.querySelectorAll("button").forEach((button) => button.classList.remove("active"));
    showDefaultPanel();
    stopAudio();
  }

  function hideRouteGradually() {
    const footprints = [...routeFootprints.querySelectorAll(".route-footprint")];

    if (routePath.getAttribute("d")) {
      const length = routePath.getTotalLength();
      routePath.classList.add("leaving");
      routePath.style.transition = `stroke-dashoffset ${mapConfig.routeExitDuration}ms ease-in-out, opacity ${mapConfig.routeExitDuration}ms ease-in-out`;
      routePath.style.strokeDasharray = length;
      routePath.style.strokeDashoffset = length;
    }

    footprints.forEach((footprint, index) => {
      const reverseIndex = footprints.length - 1 - index;
      const delay = footprints.length <= 1 ? 0 : (mapConfig.routeExitDuration / (footprints.length - 1)) * reverseIndex;
      footprint.style.opacity = "0.95";
      footprint.style.transform = "scale(1)";
      footprint.style.animation = `routeFootprintHide 280ms ease-in ${Math.round(delay)}ms both`;
    });

    highlightLayer.querySelectorAll(".office-highlight").forEach((highlight) => highlight.classList.add("leaving"));
    controls.querySelectorAll("button").forEach((button) => button.classList.remove("active"));

    window.clearTimeout(resetTimer);
    resetTimer = window.setTimeout(clearRouteDisplay, mapConfig.routeExitDuration);
  }

  function scheduleRouteReset() {
    window.clearTimeout(exitTimer);
    window.clearTimeout(resetTimer);
    exitTimer = window.setTimeout(hideRouteGradually, mapConfig.routeVisibleTime);
  }

  function playRouteAudio(route) {
    stopAudio();

    if (!route.audio) {
      return;
    }

    activeAudio = new Audio(route.audio);
    activeAudio.preload = "auto";
    activeAudio.play().catch(() => {
      activeAudio = null;
    });
  }

  function selectRoute(route) {
    window.clearTimeout(exitTimer);
    window.clearTimeout(resetTimer);
    stopAudio();

    routePath.classList.remove("leaving");
    routePath.style.opacity = "";

    if (mapConfig.routeStyle === "line-and-assets") {
      routePath.setAttribute("d", routePathFromNodes(route.nodes));
      const length = routePath.getTotalLength();
      routePath.style.transition = "none";
      routePath.style.strokeDasharray = "12 12";
      routePath.style.strokeDashoffset = length;
      routePath.getBoundingClientRect();
      routePath.style.transition = "stroke-dashoffset 1.25s ease-in-out";
      routePath.style.strokeDashoffset = "0";
    } else {
      routePath.removeAttribute("d");
    }

    renderFootprints({
      parent: routeFootprints,
      catalog,
      route,
      assetSize: route.assetSize || mapConfig.routeAssetSize,
      stepDistance: mapConfig.routeStepDistance,
      revealTime: mapConfig.routeRevealTime,
      className: "route-footprint"
    });

    renderHighlights(route.id);
    controls.querySelectorAll("button").forEach((button) => {
      button.classList.toggle("active", button.dataset.routeId === route.id);
    });
    showRoutePanel(route);
    playRouteAudio(route);
    scheduleRouteReset();
  }

  function renderButtons() {
    const buttons = mapConfig.routes
      .filter((route) => !route.archived)
      .map((route) => {
        const button = document.createElement("button");
        button.className = "office-button";
        button.type = "button";
        button.dataset.routeId = route.id;
        button.textContent = route.name;
        button.style.background = route.buttonColor || "#147a69";
        button.addEventListener("click", () => selectRoute(route));
        return button;
      });

    controls.replaceChildren(...buttons);
  }

  function keyboardRouteControl(event) {
    const buttons = [...controls.querySelectorAll("button")];
    if (!buttons.length || event.defaultPrevented) return;
    const currentIndex = Math.max(0, buttons.indexOf(document.activeElement));
    const movement = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 }[event.key];
    if (movement) { event.preventDefault(); buttons[(currentIndex + movement + buttons.length) % buttons.length].focus(); return; }
    if (/^[D-Zd-z1-9]$/.test(event.key)) { event.preventDefault(); buttons[currentIndex].click(); }
  }

  renderButtons();
  document.addEventListener("keydown", keyboardRouteControl);
  renderHighlights();
  renderDecorations({ parent: decorationLayer, catalog, decorations: mapConfig.decorations || [] });
  renderMapMarkers({ parent: markerLayer, catalog, markers: mapConfig.markers });
  showDefaultPanel();
}
