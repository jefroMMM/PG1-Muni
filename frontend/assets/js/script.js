const routePath = document.getElementById("routePath");
const routeLayer = document.getElementById("routeLayer");
const debugToggle = document.getElementById("debugToggle");
const traceToggle = document.getElementById("traceToggle");
const debugOutput = document.getElementById("debugOutput");
const debugMarkers = document.getElementById("debugMarkers");
const routeFootprints = document.getElementById("routeFootprints");
const welcomeContent = document.getElementById("welcomeContent");
const traceLayer = document.getElementById("traceLayer");
const traceLine = document.getElementById("traceLine");
const tracePoints = document.getElementById("tracePoints");
const traceReadouts = document.getElementById("traceReadouts");
const buttons = document.querySelectorAll(".office-button");
const highlights = document.querySelectorAll(".office-highlight");
const svgNamespace = "http://www.w3.org/2000/svg";

let activeRouteName = "contaduria";
let activeMarker = null;
let markerOffset = { x: 0, y: 0 };
let markerWasDragged = false;
let suppressNextMapClick = false;
let routeResetTimer = null;

const defaultWelcomeContent = welcomeContent.innerHTML;
const routeDuration = 15000;
const routeAudio = {
  contaduria: new Audio("assets/Audios/AudioContaduria.mp3")
};

routeAudio.contaduria.preload = "auto";

// Base SVG: 2000 x 1000. La imagen ocupa toda la base para evitar margenes laterales.
// El punto inicial es la Entrada y los tramos siguen pasillos visibles.
const routes = {
  contaduria: "M 1024 714 L 652 714 L 658 332 L 565 331",
  administracion: "M 1024 714 L 652 714 L 656 448 L 549 447",
  sala: "M 1024 714 L 675 714 L 680 287",
  rrhh: "M 1024 714 L 1394 714 L 1386 329 L 1490 329",
  gerencia: "M 1024 714 L 1394 714 L 1390 449 L 1482 447"
};

const footprintImages = {
  up: "assets/images/huellas%20sin%20fondo%20hacia%20arriba.png",
  down: "assets/images/huellas%20sin%20fondo%20abajo.png",
  right: "assets/images/huellas%20sin%20fondo%20derecha.png",
  left: "assets/images/huellas%20sin%20fondo%20izquierda.png"
};

const footprintSize = 68;
const footprintRevealTime = 5000;
const routeExitDuration = 4000;

function getSvgPoint(event) {
  const point = routeLayer.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(routeLayer.getScreenCTM().inverse());
}

function getRoutePoints(route) {
  const values = route.match(/[ML]\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)/g) || [];

  return values.map((value) => {
    const coordinates = value.match(/-?\d+(?:\.\d+)?/g).map(Number);
    return { x: coordinates[0], y: coordinates[1] };
  });
}

function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(svgNamespace, tagName);

  Object.entries(attributes).forEach(([name, value]) => {
    if (name === "xlink:href") {
      element.setAttributeNS("http://www.w3.org/1999/xlink", name, value);
      return;
    }

    element.setAttribute(name, value);
  });

  return element;
}

function getSegmentDirection(start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;

  if (Math.abs(dx) >= Math.abs(dy)) {
    return dx >= 0 ? "right" : "left";
  }

  return dy >= 0 ? "down" : "up";
}

function renderRouteFootprints(routeName) {
  const points = getRoutePoints(routes[routeName]);
  const footprints = [];

  for (let index = 0; index < points.length - 1; index += 1) {
    const start = points[index];
    const end = points[index + 1];
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    const steps = Math.max(1, Math.floor(length / 46));
    const direction = getSegmentDirection(start, end);

    for (let step = 1; step <= steps; step += 1) {
      const ratio = step / (steps + 1);
      const x = start.x + dx * ratio;
      const y = start.y + dy * ratio;
      const footprint = createSvgElement("image", {
        class: "route-footprint",
        href: footprintImages[direction],
        "xlink:href": footprintImages[direction],
        x: Math.round(x - footprintSize / 2),
        y: Math.round(y - footprintSize / 2),
        width: footprintSize,
        height: footprintSize,
        preserveAspectRatio: "xMidYMid meet"
      });

      footprints.push(footprint);
    }
  }

  footprints.forEach((footprint, index) => {
    const delay = footprints.length <= 1 ? 0 : (footprintRevealTime / (footprints.length - 1)) * index;
    footprint.style.animationDelay = `${Math.round(delay)}ms`;
  });

  routeFootprints.replaceChildren(...footprints);
}

function updateMarkerPosition(marker, x, y) {
  marker.dataset.x = Math.round(x);
  marker.dataset.y = Math.round(y);
  marker.setAttribute("transform", `translate(${Math.round(x)} ${Math.round(y)})`);
  marker.querySelector(".marker-x-input").value = Math.round(x);
  marker.querySelector(".marker-y-input").value = Math.round(y);

  if (marker.classList.contains("trace-marker")) {
    updateTraceLine();
  }

  if (marker.classList.contains("debug-marker-route")) {
    updateRouteFromDebugMarkers(marker.dataset.routeName);
  }
}

function addCoordinateMarker(parent, x, y, type = "manual", extraClass = "") {
  const marker = createSvgElement("g", {
    class: `debug-marker debug-marker-${type} ${extraClass}`.trim(),
    transform: `translate(${Math.round(x)} ${Math.round(y)})`
  });

  marker.dataset.x = Math.round(x);
  marker.dataset.y = Math.round(y);
  marker.dataset.type = type;

  const dot = createSvgElement("circle", {
    class: "debug-marker-dot",
    cx: 0,
    cy: 0,
    r: 9
  });
  const editorObject = createSvgElement("foreignObject", {
    class: "marker-editor-object",
    x: 14,
    y: -42,
    width: 200,
    height: 42
  });
  const editor = document.createElement("div");
  editor.className = "marker-editor";
  editor.innerHTML = `
    <label>x<input class="marker-x-input" type="number" min="0" max="2000" step="1" value="${Math.round(x)}"></label>
    <label>y<input class="marker-y-input" type="number" min="0" max="1000" step="1" value="${Math.round(y)}"></label>
    <button class="marker-delete-button" type="button" aria-label="Borrar marca">x</button>
  `;
  editorObject.appendChild(editor);

  marker.append(dot, editorObject);
  parent.appendChild(marker);

  return marker;
}

function addDebugMarker(x, y, type = "manual") {
  return addCoordinateMarker(debugMarkers, x, y, type);
}

function clearRouteDebugMarkers() {
  debugMarkers
    .querySelectorAll(".debug-marker-route")
    .forEach((marker) => marker.remove());
}

function renderRouteDebugMarkers(routeName) {
  clearRouteDebugMarkers();

  if (!debugToggle.checked) {
    return;
  }

  getRoutePoints(routes[routeName]).forEach((point, index) => {
    const marker = addDebugMarker(point.x, point.y, "route");
    marker.dataset.routeName = routeName;
    marker.dataset.pointIndex = index;
  });
}

function updateRouteFromDebugMarkers(routeName) {
  if (!routeName || routeName !== activeRouteName) {
    return;
  }

  const markers = [...debugMarkers.querySelectorAll(`.debug-marker-route[data-route-name="${routeName}"]`)]
    .sort((first, second) => Number(first.dataset.pointIndex) - Number(second.dataset.pointIndex));

  if (!markers.length) {
    return;
  }

  routes[routeName] = markers
    .map((marker, index) => `${index === 0 ? "M" : "L"} ${marker.dataset.x} ${marker.dataset.y}`)
    .join(" ");

  routePath.setAttribute("d", routes[routeName]);
  renderRouteFootprints(routeName);
}

function removeDebugMarkerFromEvent(event) {
  const deleteButton = event.target.closest(".marker-delete-button");
  const marker = event.target.closest(".debug-marker");

  if (!deleteButton || !marker) {
    return false;
  }

  marker.remove();
  updateTraceLine();
  suppressNextMapClick = true;
  event.stopPropagation();
  return true;
}

function getTracePointMarkers() {
  return [...tracePoints.querySelectorAll(".trace-marker")];
}

function getTraceAngle() {
  const markers = getTracePointMarkers();

  if (markers.length !== 2) {
    return null;
  }

  const [start, end] = markers;
  const dx = Number(end.dataset.x) - Number(start.dataset.x);
  const dy = Number(end.dataset.y) - Number(start.dataset.y);
  return Math.round(Math.atan2(Math.abs(dy), Math.abs(dx)) * 180 / Math.PI);
}

function getTraceAngleText() {
  const angle = getTraceAngle();
  return angle === null ? "" : `${angle} grados`;
}

function updateTraceLine() {
  const markers = getTracePointMarkers();
  traceReadouts.replaceChildren();

  if (markers.length !== 2) {
    traceLine.classList.remove("visible");
    if (traceToggle.checked) {
      debugOutput.textContent = "Trazado: marca dos puntos para calcular el angulo.";
    }
    return;
  }

  const [start, end] = markers;
  traceLine.setAttribute("x1", start.dataset.x);
  traceLine.setAttribute("y1", start.dataset.y);
  traceLine.setAttribute("x2", end.dataset.x);
  traceLine.setAttribute("y2", end.dataset.y);
  traceLine.classList.add("visible");

  if (traceToggle.checked) {
    debugOutput.textContent = `Angulo entre puntos: ${getTraceAngleText()}`;
  }
}

function addTracePoint(x, y) {
  if (getTracePointMarkers().length >= 2) {
    return;
  }

  addCoordinateMarker(tracePoints, x, y, "trace-point", "trace-marker");
  updateTraceLine();
}

function addTraceReadout(x, y) {
  traceReadouts.replaceChildren();
  const marker = addCoordinateMarker(traceReadouts, x, y, "trace-readout", "trace-readout");
  const editor = marker.querySelector(".marker-editor");
  const angle = document.createElement("span");
  angle.className = "marker-angle";
  angle.textContent = getTraceAngleText();

  marker.querySelector(".marker-editor-object").setAttribute("width", 265);
  editor.insertBefore(angle, editor.querySelector(".marker-delete-button"));
}

function setDebugMode(enabled) {
  debugToggle.checked = enabled;
  debugOutput.hidden = !enabled && !traceToggle.checked;
  debugMarkers.classList.toggle("visible", enabled);

  if (enabled) {
    debugOutput.textContent = "Haz clic para marcar coordenadas. Arrastra marcas o usa la x para borrar.";
    renderRouteDebugMarkers(activeRouteName);
  } else {
    debugMarkers.replaceChildren();
  }
}

function setTraceMode(enabled) {
  traceToggle.checked = enabled;
  traceLayer.classList.toggle("visible", enabled);
  debugOutput.hidden = !enabled && !debugToggle.checked;

  if (enabled) {
    debugOutput.textContent = "Trazado: marca dos puntos. Toca la linea para ver coordenadas.";
  } else {
    tracePoints.replaceChildren();
    traceReadouts.replaceChildren();
    traceLine.classList.remove("visible");
  }
}

function stopRouteAudio() {
  Object.values(routeAudio).forEach((audio) => {
    audio.pause();
    audio.currentTime = 0;
  });
}

function showDefaultWelcomeContent() {
  welcomeContent.classList.remove("hidden");
  welcomeContent.innerHTML = defaultWelcomeContent;
}

function showRoutePanel(routeName) {
  if (routeName === "contaduria") {
    welcomeContent.classList.remove("hidden");
    welcomeContent.innerHTML = `
      <p class="welcome-kicker">Ruta a Contadur&iacute;a</p>
      <p class="route-instruction">Gira a la izquierda, contin&uacute;a hasta el final del pasillo. Luego, gira a la derecha. La oficina de Contadur&iacute;a se encuentra en la primera puerta, a mano izquierda.</p>
    `;
    return;
  }

  welcomeContent.classList.add("hidden");
}

function clearRouteDisplay() {
  routePath.removeAttribute("d");
  routePath.style.transition = "none";
  routePath.style.strokeDashoffset = "0";
  routePath.classList.remove("leaving");
  routeFootprints.replaceChildren();

  highlights.forEach((highlight) => highlight.classList.remove("active", "leaving"));
  buttons.forEach((button) => button.classList.remove("active"));

  if (!debugToggle.checked) {
    debugMarkers.replaceChildren();
  }

  showDefaultWelcomeContent();
}

function hideRouteGradually() {
  const length = routePath.getTotalLength();
  const footprints = [...routeFootprints.querySelectorAll(".route-footprint")];

  routePath.classList.add("leaving");
  routePath.style.transition = `stroke-dashoffset ${routeExitDuration}ms ease-in-out, opacity ${routeExitDuration}ms ease-in-out`;
  routePath.style.strokeDasharray = length;
  routePath.style.strokeDashoffset = length;

  footprints.forEach((footprint, index) => {
    const reverseIndex = footprints.length - 1 - index;
    const delay = footprints.length <= 1 ? 0 : (routeExitDuration / (footprints.length - 1)) * reverseIndex;
    footprint.style.opacity = "0.95";
    footprint.style.transform = "scale(1)";
    footprint.style.animation = `routeFootprintHide 280ms ease-in ${Math.round(delay)}ms both`;
  });

  highlights.forEach((highlight) => highlight.classList.add("leaving"));
  buttons.forEach((button) => button.classList.remove("active"));

  window.clearTimeout(routeResetTimer);
  routeResetTimer = window.setTimeout(() => {
    clearRouteDisplay();
  }, routeExitDuration);
}

function scheduleRouteReset() {
  window.clearTimeout(routeResetTimer);
  routeResetTimer = window.setTimeout(() => {
    hideRouteGradually();
  }, routeDuration);
}

function playRouteAudio(routeName) {
  stopRouteAudio();

  const audio = routeAudio[routeName];
  if (!audio) {
    return;
  }

  audio.play().catch(() => {
    // El navegador puede bloquear audio si no considera el clic como gesto valido.
  });
}

function selectRoute(routeName) {
  const route = routes[routeName];

  activeRouteName = routeName;
  window.clearTimeout(routeResetTimer);
  stopRouteAudio();

  routePath.classList.remove("leaving");
  highlights.forEach((highlight) => highlight.classList.remove("leaving"));
  routePath.setAttribute("d", route);

  const length = routePath.getTotalLength();
  routePath.style.transition = "none";
  routePath.style.strokeDasharray = "12 12";
  routePath.style.strokeDashoffset = length;

  // Reinicia la animacion del trazo cada vez que se presiona un boton.
  routePath.getBoundingClientRect();
  routePath.style.transition = "stroke-dashoffset 1.25s ease-in-out";
  routePath.style.strokeDashoffset = "0";

  highlights.forEach((highlight) => highlight.classList.remove("active"));
  document.getElementById(`highlight-${routeName}`).classList.add("active");

  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset.route === routeName);
  });

  renderRouteFootprints(routeName);
  if (debugToggle.checked) {
    renderRouteDebugMarkers(routeName);
  }
  showRoutePanel(routeName);
  playRouteAudio(routeName);
  scheduleRouteReset();
}

buttons.forEach((button) => {
  button.addEventListener("click", () => selectRoute(button.dataset.route));
});

debugToggle.addEventListener("change", () => {
  setDebugMode(debugToggle.checked);
});

traceToggle.addEventListener("change", () => {
  setTraceMode(traceToggle.checked);
});

routeLayer.addEventListener("pointerdown", (event) => {
  if (!debugToggle.checked && !traceToggle.checked) {
    return;
  }

  if (removeDebugMarkerFromEvent(event)) {
    return;
  }

  if (event.target.closest(".marker-x-input, .marker-y-input, .marker-delete-button")) {
    return;
  }

  const marker = event.target.closest(".debug-marker");

  if (!marker) {
    return;
  }

  const svgPoint = getSvgPoint(event);
  activeMarker = marker;
  markerWasDragged = false;
  markerOffset = {
    x: svgPoint.x - Number(marker.dataset.x),
    y: svgPoint.y - Number(marker.dataset.y)
  };

  marker.classList.add("dragging");
  marker.setPointerCapture(event.pointerId);
  event.stopPropagation();
});

routeLayer.addEventListener("pointermove", (event) => {
  if (!activeMarker) {
    return;
  }

  const svgPoint = getSvgPoint(event);
  const x = svgPoint.x - markerOffset.x;
  const y = svgPoint.y - markerOffset.y;

  markerWasDragged = true;
  updateMarkerPosition(activeMarker, x, y);

  if (!activeMarker.classList.contains("trace-marker") || getTracePointMarkers().length < 2) {
    debugOutput.textContent = `x: ${Math.round(x)}, y: ${Math.round(y)}`;
  }
});

routeLayer.addEventListener("pointerup", (event) => {
  if (!activeMarker) {
    return;
  }

  activeMarker.classList.remove("dragging");
  activeMarker.releasePointerCapture(event.pointerId);
  activeMarker = null;
  event.stopPropagation();
});

routeLayer.addEventListener("click", (event) => {
  if (suppressNextMapClick) {
    suppressNextMapClick = false;
    return;
  }

  if ((!debugToggle.checked && !traceToggle.checked) || markerWasDragged) {
    markerWasDragged = false;
    return;
  }

  if (removeDebugMarkerFromEvent(event)) {
    return;
  }

  if (event.target.closest(".marker-x-input, .marker-y-input, .marker-delete-button")) {
    return;
  }

  if (event.target.closest(".debug-marker")) {
    return;
  }

  const svgPoint = getSvgPoint(event);
  const x = Math.round(svgPoint.x);
  const y = Math.round(svgPoint.y);

  if (traceToggle.checked) {
    if (event.target === traceLine) {
      debugOutput.textContent = `Linea x: ${x}, y: ${y}, angulo: ${getTraceAngleText()}`;
      addTraceReadout(x, y);
      return;
    }

    if (getTracePointMarkers().length < 2) {
      addTracePoint(x, y);
    }

    if (getTracePointMarkers().length < 2) {
      debugOutput.textContent = `Punto trazado x: ${x}, y: ${y}. Falta el segundo punto.`;
    }
  }

  if (debugToggle.checked) {
    addDebugMarker(x, y, "manual");

    if (!traceToggle.checked || getTracePointMarkers().length < 2) {
      debugOutput.textContent = `x: ${x}, y: ${y}`;
    }

    console.log(`Coordenada SVG: ${x}, ${y}`);
  }
});

function handleMarkerCoordinateEdit(event) {
  if (!event.target.matches(".marker-x-input, .marker-y-input")) {
    return;
  }

  const marker = event.target.closest(".debug-marker");
  const xInput = marker.querySelector(".marker-x-input");
  const yInput = marker.querySelector(".marker-y-input");
  const x = Math.max(0, Math.min(2000, Number(xInput.value) || 0));
  const y = Math.max(0, Math.min(1000, Number(yInput.value) || 0));

  updateMarkerPosition(marker, x, y);
  debugOutput.hidden = false;
  debugOutput.textContent = marker.classList.contains("trace-marker")
    ? `Angulo entre puntos: ${getTraceAngleText()}`
    : `Punto editado x: ${x}, y: ${y}`;
}

routeLayer.addEventListener("input", handleMarkerCoordinateEdit);
routeLayer.addEventListener("change", handleMarkerCoordinateEdit);
