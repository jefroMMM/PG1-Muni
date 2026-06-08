const maprLayer = document.getElementById("maprLayer");
const debugToggle = document.getElementById("debugToggle");
const traceToggle = document.getElementById("traceToggle");
const debugOutput = document.getElementById("debugOutput");
const debugMarkers = document.getElementById("debugMarkers");
const maprPanelContent = document.getElementById("maprPanelContent");
const mapRouteFootprints = document.getElementById("mapRouteFootprints");
const traceLine = document.getElementById("traceLine");
const tracePoints = document.getElementById("tracePoints");
const traceReadouts = document.getElementById("traceReadouts");
const svgNs = "http://www.w3.org/2000/svg";

let activeMarker = null;
let markerOffset = { x: 0, y: 0 };
let markerWasDragged = false;
let suppressNextMapClick = false;
let activeRouteName = null;

const defaultPanelContent = maprPanelContent.innerHTML;
const routeNames = {
  municipalidad: "Municipalidad de Retalhuleu",
  renap: "Registro Nacional de las Personas",
  pnc: "Policía Nacional Civil"
};

const routeFootprintPoints = {
  municipalidad: [
    { x: 1521, y: 676 },
    { x: 1468, y: 732 },
    { x: 1541, y: 808 }
  ],
  renap: [
    { x: 1525, y: 671 },
    { x: 1584, y: 603 },
    { x: 1519, y: 506 },
    { x: 1448, y: 557 },
    { x: 1329, y: 409 },
    { x: 1286, y: 324 },
    { x: 1205, y: 342 },
    { x: 730, y: 398 },
    { x: 635, y: 443 },
    { x: 573, y: 497 }
  ]
};

const routeSegmentSprites = {
  renap: [
    "huellas",
    "tucUpLeft",
    "tucLeft",
    "tucUpRight",
    "tucUpRight",
    "tucLeft",
    "tucLeft",
    "tucLeft",
    "tucLeft"
  ]
};

const footprintImages = {
  up: "Imagenes-MapaR/huellas%20sin%20fondo%20hacia%20arriba.png",
  down: "Imagenes-MapaR/huellas%20sin%20fondo%20abajo.png",
  right: "Imagenes-MapaR/huellas%20sin%20fondo%20derecha.png",
  left: "Imagenes-MapaR/huellas%20sin%20fondo%20izquierda.png",
  tucUpLeft: "Imagenes-MapaR/tuc%20tuc%20mirando%20arriba%20izquierda.png",
  tucLeft: "Imagenes-MapaR/tuc%20tuc%20izquierda.png",
  tucUpRight: "Imagenes-MapaR/tuctuc%20derecha%20arriba.png",
  tucRight: "Imagenes-MapaR/tuctuc%20derecha.png"
};

const footprintSize = 40;
const footprintRevealTime = 5000;

function getSvgPoint(event) {
  const point = maprLayer.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(maprLayer.getScreenCTM().inverse());
}

function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(svgNs, tagName);

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
  const points = routeFootprintPoints[routeName];
  const segmentSprites = routeSegmentSprites[routeName] || [];
  const footprints = [];

  if (!points) {
    mapRouteFootprints.replaceChildren();
    return;
  }

  for (let index = 0; index < points.length - 1; index += 1) {
    const start = points[index];
    const end = points[index + 1];
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    const steps = Math.max(1, Math.floor(length / 40));
    const direction = getSegmentDirection(start, end);
    const spriteKey = segmentSprites[index];
    const sprite = spriteKey === "huellas" || !spriteKey
      ? footprintImages[direction]
      : footprintImages[spriteKey];

    for (let step = 1; step <= steps; step += 1) {
      const ratio = step / (steps + 1);
      const x = start.x + dx * ratio;
      const y = start.y + dy * ratio;
      const footprint = createSvgElement("image", {
        class: "map-route-footprint",
        href: sprite,
        "xlink:href": sprite,
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

  mapRouteFootprints.replaceChildren(...footprints);
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

function updateMarkerPosition(marker, x, y) {
  const cleanX = Math.max(0, Math.min(2000, Math.round(x)));
  const cleanY = Math.max(0, Math.min(1000, Math.round(y)));

  marker.dataset.x = cleanX;
  marker.dataset.y = cleanY;
  marker.setAttribute("transform", `translate(${cleanX} ${cleanY})`);
  marker.querySelector(".marker-x-input").value = cleanX;
  marker.querySelector(".marker-y-input").value = cleanY;

  if (marker.classList.contains("trace-marker")) {
    updateTraceLine();
  }

  if (marker.classList.contains("route-node-marker")) {
    updateRouteFromDebugNodes(marker.dataset.routeName);
  }
}

function addCoordinateMarker(parent, x, y, label, className) {
  const marker = createSvgElement("g", {
    class: `debug-marker ${className}`,
    transform: `translate(${x} ${y})`,
    "data-x": x,
    "data-y": y
  });

  const dot = createSvgElement("circle", {
    class: "debug-marker-dot",
    r: 10
  });

  const editorObject = createSvgElement("foreignObject", {
    class: "marker-editor-object",
    x: 14,
    y: -18,
    width: 205,
    height: 44
  });

  const editor = document.createElement("div");
  editor.className = "marker-editor";
  editor.innerHTML = `
    <label>X <input class="marker-x-input" type="number" min="0" max="2000" value="${x}"></label>
    <label>Y <input class="marker-y-input" type="number" min="0" max="1000" value="${y}"></label>
    <button class="marker-delete-button" type="button" aria-label="Borrar ${label}">x</button>
  `;

  editorObject.appendChild(editor);
  marker.append(dot, editorObject);
  parent.appendChild(marker);
  return marker;
}

function addDebugMarker(x, y) {
  return addCoordinateMarker(debugMarkers, x, y, "punto", "manual-marker");
}

function renderRouteDebugNodes(routeName) {
  const points = routeFootprintPoints[routeName] || [];
  const nodes = points.map((point, index) => {
    const marker = addCoordinateMarker(debugMarkers, point.x, point.y, `punto ${index + 1}`, "route-node-marker");
    marker.dataset.routeName = routeName;
    marker.dataset.pointIndex = index;
    return marker;
  });

  debugMarkers.replaceChildren(...nodes);
  renderDebugPanel(routeName);
}

function updateRouteFromDebugNodes(routeName) {
  const nodes = [...debugMarkers.querySelectorAll(`.route-node-marker[data-route-name="${routeName}"]`)]
    .sort((first, second) => Number(first.dataset.pointIndex) - Number(second.dataset.pointIndex));

  if (!nodes.length) {
    return;
  }

  routeFootprintPoints[routeName] = nodes.map((node) => ({
    x: Number(node.dataset.x),
    y: Number(node.dataset.y)
  }));

  if (activeRouteName === routeName) {
    renderRouteFootprints(routeName);
    renderDebugPanel(routeName);
  }
}

function renderDefaultPanel() {
  maprPanelContent.innerHTML = defaultPanelContent;
}

function renderDebugPanel(routeName) {
  const points = routeFootprintPoints[routeName] || [];
  const title = routeNames[routeName] || "Ruta sin seleccionar";

  if (!debugToggle.checked) {
    return;
  }

  if (!points.length) {
    maprPanelContent.innerHTML = `
      <p>Modo depuraci&oacute;n</p>
      <h1>Nodos</h1>
      <span>Selecciona una dependencia para ver los puntos del recorrido.</span>
    `;
    return;
  }

  const items = points
    .map((point, index) => `<li><strong>Nodo ${index + 1}</strong><span>x: ${point.x}, y: ${point.y}</span></li>`)
    .join("");

  maprPanelContent.innerHTML = `
    <p>Modo depuraci&oacute;n</p>
    <h1>${title}</h1>
    <ul class="debug-node-list">${items}</ul>
  `;
}

function addTracePoint(x, y) {
  if (getTracePointMarkers().length >= 2) {
    return;
  }

  addCoordinateMarker(tracePoints, x, y, "punto de trazado", "trace-marker");
  updateTraceLine();
}

function addTraceReadout(x, y) {
  traceReadouts.replaceChildren();
  const marker = addCoordinateMarker(traceReadouts, x, y, "lectura", "trace-readout");
  const editor = marker.querySelector(".marker-editor");
  const angle = document.createElement("span");
  angle.className = "marker-angle";
  angle.textContent = getTraceAngleText();

  marker.querySelector(".marker-editor-object").setAttribute("width", 265);
  editor.insertBefore(angle, editor.querySelector(".marker-delete-button"));
}

function removeMarkerFromEvent(event) {
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

function setDebugMode(enabled) {
  debugToggle.checked = enabled;
  debugOutput.hidden = !enabled && !traceToggle.checked;

  if (enabled) {
    debugOutput.textContent = "Haz clic para marcar coordenadas. Arrastra marcas o usa la x para borrar.";
    if (activeRouteName) {
      renderRouteDebugNodes(activeRouteName);
    } else {
      renderDebugPanel(null);
    }
  } else {
    debugMarkers.replaceChildren();
    renderDefaultPanel();
  }
}

function setTraceMode(enabled) {
  traceToggle.checked = enabled;
  debugOutput.hidden = !enabled && !debugToggle.checked;

  if (enabled) {
    debugOutput.textContent = "Trazado: marca dos puntos. Toca la linea para ver coordenadas.";
  } else {
    tracePoints.replaceChildren();
    traceReadouts.replaceChildren();
    traceLine.classList.remove("visible");
  }
}

debugToggle.addEventListener("change", () => setDebugMode(debugToggle.checked));
traceToggle.addEventListener("change", () => setTraceMode(traceToggle.checked));

maprLayer.addEventListener("pointerdown", (event) => {
  if (!debugToggle.checked && !traceToggle.checked) {
    return;
  }

  if (removeMarkerFromEvent(event)) {
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

maprLayer.addEventListener("pointermove", (event) => {
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

maprLayer.addEventListener("pointerup", (event) => {
  if (!activeMarker) {
    return;
  }

  activeMarker.classList.remove("dragging");
  activeMarker.releasePointerCapture(event.pointerId);
  activeMarker = null;
  event.stopPropagation();
});

maprLayer.addEventListener("click", (event) => {
  if (suppressNextMapClick) {
    suppressNextMapClick = false;
    return;
  }

  if ((!debugToggle.checked && !traceToggle.checked) || markerWasDragged) {
    markerWasDragged = false;
    return;
  }

  if (removeMarkerFromEvent(event)) {
    return;
  }

  if (event.target.closest(".marker-x-input, .marker-y-input, .marker-delete-button, .debug-marker")) {
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
    addDebugMarker(x, y);

    if (!traceToggle.checked || getTracePointMarkers().length < 2) {
      debugOutput.textContent = `x: ${x}, y: ${y}`;
    }
  }
});

function handleMarkerCoordinateEdit(event) {
  if (!event.target.matches(".marker-x-input, .marker-y-input")) {
    return;
  }

  const marker = event.target.closest(".debug-marker");
  const xInput = marker.querySelector(".marker-x-input");
  const yInput = marker.querySelector(".marker-y-input");

  updateMarkerPosition(marker, Number(xInput.value) || 0, Number(yInput.value) || 0);
  debugOutput.hidden = false;
  debugOutput.textContent = marker.classList.contains("trace-marker")
    ? `Angulo entre puntos: ${getTraceAngleText()}`
    : `Punto editado x: ${marker.dataset.x}, y: ${marker.dataset.y}`;
}

maprLayer.addEventListener("input", handleMarkerCoordinateEdit);
maprLayer.addEventListener("change", handleMarkerCoordinateEdit);

document.querySelectorAll("[data-map-route]").forEach((button) => {
  button.addEventListener("click", () => {
    activeRouteName = button.dataset.mapRoute;
    mapRouteFootprints.replaceChildren();
    renderRouteFootprints(activeRouteName);

    if (debugToggle.checked) {
      renderRouteDebugNodes(activeRouteName);
    } else {
      renderDefaultPanel();
    }
  });
});
