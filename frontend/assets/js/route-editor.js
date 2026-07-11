import { loadRouteConfig, saveRouteConfig } from "./shared/config-api.js";
import {
  clampPoint,
  createSvgElement,
  findAsset,
  generateId,
  getSvgPoint,
  normalizeSegmentAssets,
  renderDecorations,
  renderFootprints,
  renderMapMarkers,
  routePathFromNodes
} from "./shared/map-utils.js";

const mapKey = window.location.pathname.toLowerCase().startsWith("/mapar") ? "mapar" : "terminal";
const mapHome = mapKey === "mapar" ? "/MapaR/" : "/";

const elements = {
  backLink: document.getElementById("backLink"),
  editorTitle: document.getElementById("editorTitle"),
  saveStatus: document.getElementById("saveStatus"),
  routeInspector: document.getElementById("routeInspector"),
  mapImage: document.getElementById("editorMapImage"),
  layer: document.getElementById("editorLayer"),
  highlightLayer: document.getElementById("editorHighlightLayer"),
  routePath: document.getElementById("editorRoutePath"),
  footprints: document.getElementById("editorFootprints"),
  markerLayer: document.getElementById("editorMarkerLayer"),
  decorationLayer: document.getElementById("editorDecorationLayer"),
  nodeLayer: document.getElementById("editorNodeLayer"),
  placedIconLayer: document.getElementById("editorPlacedIconLayer"),
  placedDecorationLayer: document.getElementById("editorPlacedDecorationLayer"),
  routeList: document.getElementById("routeList"),
  nodeList: document.getElementById("nodeList"),
  segmentAssetList: document.getElementById("segmentAssetList"),
  markerList: document.getElementById("markerList"),
  decorationList: document.getElementById("decorationList"),
  routeNameInput: document.getElementById("routeNameInput"),
  routeColorInput: document.getElementById("routeColorInput"),
  routeInstructionsInput: document.getElementById("routeInstructionsInput"),
  routeAudioSelect: document.getElementById("routeAudioSelect"),
  routeAssetSizeInput: document.getElementById("routeAssetSizeInput"),
  markerAssetSelect: document.getElementById("markerAssetSelect"),
  decorationAssetSelect: document.getElementById("decorationAssetSelect"),
  backgroundSelect: document.getElementById("backgroundSelect"),
  routeAssetUploadInput: document.getElementById("routeAssetUploadInput"),
  iconUploadInput: document.getElementById("iconUploadInput"),
  decorationUploadInput: document.getElementById("decorationUploadInput"),
  backgroundUploadInput: document.getElementById("backgroundUploadInput"),
  audioUploadInput: document.getElementById("audioUploadInput"),
  newRouteButton: document.getElementById("newRouteButton"),
  archiveRouteButton: document.getElementById("archiveRouteButton"),
  duplicateRouteButton: document.getElementById("duplicateRouteButton"),
  deleteRouteButton: document.getElementById("deleteRouteButton"),
  addNodeButton: document.getElementById("addNodeButton"),
  deleteNodeButton: document.getElementById("deleteNodeButton"),
  addIconButton: document.getElementById("addIconButton"),
  addDecorationButton: document.getElementById("addDecorationButton"),
  nodeToolButton: document.getElementById("nodeToolButton"),
  iconToolButton: document.getElementById("iconToolButton"),
  saveButton: document.getElementById("saveButton")
};

let config;
let mapConfig;
let activeRouteId = "";
let activeTool = "node";
let activeMode = "routes";
let pendingNodeClick = false;
let pendingIconClick = false;
let pendingDecorationClick = false;
let dragState = null;
let hasUnsavedChanges = false;

function activeRoute() {
  return mapConfig.routes.find((route) => route.id === activeRouteId) || mapConfig.routes[0];
}

function fallbackRouteAssetId() {
  return mapKey === "mapar" ? "mapr-footprints-auto" : "footprints-auto";
}

function setDirty() {
  hasUnsavedChanges = true;
  elements.saveStatus.textContent = "Cambios sin guardar";
  elements.saveStatus.classList.add("dirty");
}

function setSaved() {
  hasUnsavedChanges = false;
  elements.saveStatus.textContent = "Guardado";
  elements.saveStatus.classList.remove("dirty");
}

async function uploadFile(file, kind) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("kind", kind);

  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error("No se pudo subir el archivo");
  }

  return response.json();
}

function syncActiveRouteFromInputs() {
  const route = activeRoute();
  if (!route) {
    return;
  }

  route.name = elements.routeNameInput.value.trim() || "Ruta sin nombre";
  route.buttonColor = elements.routeColorInput.value || "#147a69";
  route.instructions = elements.routeInstructionsInput.value.trim();
  setDirty();
  renderRouteList();
}

function syncRouteAssetSize() {
  const route = activeRoute();
  if (!route) {
    return;
  }

  route.assetSize = Math.max(12, Math.min(180, Number(elements.routeAssetSizeInput.value) || mapConfig.routeAssetSize));
  setDirty();
  renderRouteGraphics();
}

function syncRouteAudio() {
  const route = activeRoute();
  if (!route) {
    return;
  }

  route.audio = elements.routeAudioSelect.value;
  setDirty();
}

function rotate45(value = 0) {
  return (Number(value) + 45) % 360;
}

function setMode(mode) {
  activeMode = mode;
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== mode;
  });
}

function renderRouteList() {
  const items = mapConfig.routes.map((route) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `route-list-item ${route.id === activeRouteId ? "active" : ""}`;
    button.innerHTML = `
      <span>${route.name}</span>
      <small>${route.archived ? "Archivada" : "Visible"}</small>
    `;
    button.addEventListener("click", () => {
      activeRouteId = route.id;
      renderAll();
    });
    return button;
  });

  elements.routeList.replaceChildren(...items);
}

function routeLength(nodes = []) {
  return nodes.reduce((total, point, index) => {
    if (index === 0) {
      return total;
    }

    const previous = nodes[index - 1];
    return total + Math.hypot(point.x - previous.x, point.y - previous.y);
  }, 0);
}

function renderRouteInspector() {
  const route = activeRoute();

  if (!route) {
    elements.routeInspector.innerHTML = `
      <strong>Sin ruta seleccionada</strong>
      <span>Crea una ruta para comenzar.</span>
    `;
    return;
  }

  const nodes = route.nodes || [];
  const segmentCount = Math.max(0, nodes.length - 1);
  const warnings = [];

  if (nodes.length < 2) {
    warnings.push("faltan nodos");
  }

  if ((route.segmentAssets || []).length !== segmentCount) {
    warnings.push("tramos sin asset");
  }

  if (!route.instructions?.trim()) {
    warnings.push("sin indicaciones");
  }

  elements.routeInspector.innerHTML = `
    <strong>${route.name || "Ruta sin nombre"}</strong>
    <span>${route.archived ? "Archivada" : "Visible"}</span>
    <span>${nodes.length} nodos</span>
    <span>${segmentCount} tramos</span>
    <span>${Math.round(routeLength(nodes))} px</span>
    <span>${route.audio ? "Con audio" : "Sin audio"}</span>
    ${warnings.length ? `<em>${warnings.join(" · ")}</em>` : "<em>Lista para usar</em>"}
  `;
}

function renderForm() {
  const route = activeRoute();
  const hasRoute = Boolean(route);

  [elements.routeNameInput, elements.routeColorInput, elements.routeInstructionsInput, elements.routeAudioSelect, elements.routeAssetSizeInput, elements.archiveRouteButton, elements.duplicateRouteButton, elements.deleteRouteButton, elements.addNodeButton, elements.deleteNodeButton]
    .forEach((control) => {
      control.disabled = !hasRoute;
    });

  if (!route) {
    elements.routeNameInput.value = "";
    elements.routeColorInput.value = "#147a69";
    elements.routeInstructionsInput.value = "";
    elements.routeAssetSizeInput.value = mapConfig.routeAssetSize;
    return;
  }

  normalizeSegmentAssets(route, fallbackRouteAssetId());
  elements.routeNameInput.value = route.name || "";
  elements.routeColorInput.value = route.buttonColor || "#147a69";
  elements.routeInstructionsInput.value = route.instructions || "";
  elements.routeAssetSizeInput.value = route.assetSize || mapConfig.routeAssetSize;
  elements.archiveRouteButton.textContent = route.archived ? "Desarchivar" : "Archivar";
  renderAudioSelect(route);
}

function renderAudioSelect(route) {
  const audios = config.catalog.audios || [];
  const currentAudio = route.audio || "";
  const options = [
    { name: "Sin audio", src: "" },
    ...audios
  ];

  if (currentAudio && !options.some((audio) => audio.src === currentAudio)) {
    options.push({ name: "Audio actual", src: currentAudio });
  }

  elements.routeAudioSelect.replaceChildren(...options.map((audio) => {
    const option = document.createElement("option");
    option.value = audio.src;
    option.textContent = audio.name;
    option.selected = audio.src === currentAudio;
    return option;
  }));
}

function renderNodes() {
  const route = activeRoute();
  const nodes = route?.nodes || [];
  const nodeElements = nodes.map((point, index) => {
    const marker = createSvgElement("g", {
      class: "editor-node",
      transform: `translate(${point.x} ${point.y})`,
      "data-index": index
    });
    marker.append(
      createSvgElement("circle", { r: 12 }),
      createSvgElement("text", { y: 4, "text-anchor": "middle" })
    );
    marker.querySelector("text").textContent = String(index + 1);
    return marker;
  });

  elements.nodeLayer.replaceChildren(...nodeElements);

  const rows = nodes.map((point, index) => {
    const row = document.createElement("label");
    row.className = "node-row";
    row.innerHTML = `
      <span>Nodo ${index + 1}</span>
      <input type="number" min="0" max="2000" value="${point.x}" data-node-index="${index}" data-axis="x">
      <input type="number" min="0" max="1000" value="${point.y}" data-node-index="${index}" data-axis="y">
    `;
    return row;
  });

  elements.nodeList.replaceChildren(...rows);
}

function renderSegments() {
  const route = activeRoute();
  const segments = route?.segmentAssets || [];
  const segmentOptions = route?.segmentOptions || [];
  const routeAssets = config.catalog.routeAssets || [];
  const rows = segments.map((assetId, index) => {
    const row = document.createElement("div");
    row.className = "asset-row";
    const label = document.createElement("label");
    label.className = "field-label compact-field asset-select-field";
    const select = document.createElement("select");
    select.dataset.segmentIndex = String(index);

    routeAssets.forEach((asset) => {
      const option = document.createElement("option");
      option.value = asset.id;
      option.textContent = asset.name;
      option.selected = asset.id === assetId;
      select.appendChild(option);
    });

    label.append(`Tramo ${index + 1}`, select);
    const options = segmentOptions[index] || {};
    const mirrorButton = document.createElement("button");
    mirrorButton.type = "button";
    mirrorButton.className = `mini-action ${options.mirrored ? "active" : ""}`;
    mirrorButton.dataset.segmentMirror = String(index);
    mirrorButton.textContent = "Espejo";

    const rotateButton = document.createElement("button");
    rotateButton.type = "button";
    rotateButton.className = "mini-action";
    rotateButton.dataset.segmentRotate = String(index);
    rotateButton.textContent = `${Number(options.rotation) || 0} deg`;

    row.append(label, mirrorButton, rotateButton);
    return row;
  });

  elements.segmentAssetList.replaceChildren(...rows);
}

function renderRouteGraphics() {
  const route = activeRoute();
  elements.routePath.removeAttribute("d");
  elements.footprints.replaceChildren();
  elements.highlightLayer.replaceChildren();

  if (!route) {
    return;
  }

  if (mapConfig.routeStyle === "line-and-assets") {
    elements.routePath.setAttribute("d", routePathFromNodes(route.nodes));
  }

  renderFootprints({
      parent: elements.footprints,
      catalog: config.catalog,
      route,
      assetSize: route.assetSize || mapConfig.routeAssetSize,
      stepDistance: mapConfig.routeStepDistance,
    revealTime: 0,
    className: "route-footprint editor-footprint"
  });

  if (route.highlightPolygon) {
    elements.highlightLayer.replaceChildren(createSvgElement("polygon", {
      class: "office-highlight active",
      points: route.highlightPolygon
    }));
  }
}

function renderMarkerControls() {
  const markerAssets = config.catalog.markerIcons || [];
  elements.markerAssetSelect.replaceChildren(...markerAssets.map((asset) => {
    const option = document.createElement("option");
    option.value = asset.id;
    option.textContent = asset.name;
    return option;
  }));

  const rows = (mapConfig.markers || []).map((marker) => {
    const asset = findAsset(config.catalog, marker.assetId);
    const row = document.createElement("div");
    row.className = "marker-row";
    row.innerHTML = `
      <img src="${asset?.src || ""}" alt="">
      <input type="text" value="${marker.label || ""}" data-marker-id="${marker.id}" data-field="label">
      <input type="number" min="16" max="180" value="${marker.width || 50}" data-marker-id="${marker.id}" data-field="width" title="Tamano">
      <button type="button" data-marker-mirror="${marker.id}">${marker.mirrored ? "Sin espejo" : "Espejo"}</button>
      <button type="button" data-marker-rotate="${marker.id}">${Number(marker.rotation) || 0} deg</button>
      <button type="button" data-delete-marker="${marker.id}">Borrar</button>
    `;
    return row;
  });

  elements.markerList.replaceChildren(...rows);
}

function renderDecorationControls() {
  const decorationAssets = config.catalog.decorations || [];
  elements.decorationAssetSelect.replaceChildren(...decorationAssets.map((asset) => {
    const option = document.createElement("option");
    option.value = asset.id;
    option.textContent = asset.name;
    return option;
  }));

  const rows = (mapConfig.decorations || []).map((decoration) => {
    const asset = findAsset(config.catalog, decoration.assetId);
    const row = document.createElement("div");
    row.className = "marker-row decoration-row";
    row.innerHTML = `
      <img src="${asset?.src || ""}" alt="">
      <input type="text" value="${decoration.label || ""}" data-decoration-id="${decoration.id}" data-field="label">
      <input type="number" min="16" max="260" value="${decoration.width || 80}" data-decoration-id="${decoration.id}" data-field="width" title="Tamano">
      <button type="button" data-decoration-mirror="${decoration.id}">${decoration.mirrored ? "Sin espejo" : "Espejo"}</button>
      <button type="button" data-decoration-rotate="${decoration.id}">${Number(decoration.rotation) || 0} deg</button>
      <button type="button" data-delete-decoration="${decoration.id}">Borrar</button>
    `;
    return row;
  });

  elements.decorationList.replaceChildren(...rows);
}

function renderBackgroundControls() {
  const backgrounds = config.catalog.backgrounds || [];
  elements.backgroundSelect.replaceChildren(...backgrounds.map((background) => {
    const option = document.createElement("option");
    option.value = background.src;
    option.textContent = background.name;
    option.selected = background.src === mapConfig.background;
    return option;
  }));
}

function renderPlacedIconHandles() {
  const handles = (mapConfig.markers || []).map((marker) => {
    const handle = createSvgElement("rect", {
      class: "editor-icon-handle",
      x: marker.x,
      y: marker.y,
      width: marker.width || 50,
      height: marker.height || marker.width || 50,
      "data-marker-id": marker.id
    });
    return handle;
  });

  elements.placedIconLayer.replaceChildren(...handles);
}

function renderPlacedDecorationHandles() {
  const handles = (mapConfig.decorations || []).map((decoration) => createSvgElement("rect", {
    class: "editor-icon-handle editor-decoration-handle",
    x: decoration.x,
    y: decoration.y,
    width: decoration.width || 80,
    height: decoration.height || decoration.width || 80,
    "data-decoration-id": decoration.id
  }));

  elements.placedDecorationLayer.replaceChildren(...handles);
}

function renderMarkers() {
  renderMapMarkers({ parent: elements.markerLayer, catalog: config.catalog, markers: mapConfig.markers || [] });
  renderPlacedIconHandles();
  renderMarkerControls();
}

function renderDecorationsLayer() {
  renderDecorations({
    parent: elements.decorationLayer,
    catalog: config.catalog,
    decorations: mapConfig.decorations || []
  });
  renderPlacedDecorationHandles();
  renderDecorationControls();
}

function renderAll() {
  renderRouteList();
  renderRouteInspector();
  renderForm();
  renderRouteGraphics();
  renderNodes();
  renderSegments();
  renderMarkers();
  renderDecorationsLayer();
  renderBackgroundControls();
}

function addRoute() {
  const route = {
    id: generateId("ruta"),
    name: "Nueva ruta",
    archived: false,
    buttonColor: "#147a69",
    instructions: "",
    audio: "",
    assetSize: mapConfig.routeAssetSize,
    nodes: [
      { x: 1000, y: 700 },
      { x: 1100, y: 700 }
    ],
    segmentAssets: [fallbackRouteAssetId()]
  };

  mapConfig.routes.push(route);
  activeRouteId = route.id;
  setDirty();
  renderAll();
}

function duplicateRoute() {
  const route = activeRoute();

  if (!route) {
    return;
  }

  const copy = JSON.parse(JSON.stringify(route));
  copy.id = generateId("ruta");
  copy.name = `${route.name || "Ruta"} copia`;
  copy.archived = true;
  copy.nodes = (copy.nodes || []).map((point) => ({
    x: Math.min(2000, point.x + 24),
    y: Math.min(1000, point.y + 24)
  }));

  mapConfig.routes.push(copy);
  activeRouteId = copy.id;
  setDirty();
  renderAll();
}

function deleteActiveRoute() {
  const route = activeRoute();

  if (!route || mapConfig.routes.length <= 1) {
    elements.saveStatus.textContent = "Debe quedar al menos una ruta";
    elements.saveStatus.classList.add("dirty");
    return;
  }

  const shouldDelete = window.confirm(`Borrar la ruta "${route.name}"?`);
  if (!shouldDelete) {
    return;
  }

  mapConfig.routes = mapConfig.routes.filter((item) => item.id !== route.id);
  activeRouteId = mapConfig.routes[0]?.id || "";
  setDirty();
  renderAll();
}

function addNodeAt(point) {
  const route = activeRoute();
  if (!route) {
    return;
  }

  route.nodes.push(point);
  normalizeSegmentAssets(route, fallbackRouteAssetId());
  pendingNodeClick = false;
  elements.addNodeButton.classList.remove("active");
  setDirty();
  renderAll();
}

function deleteLastNode() {
  const route = activeRoute();
  if (!route || route.nodes.length <= 2) {
    return;
  }

  route.nodes.pop();
  normalizeSegmentAssets(route, fallbackRouteAssetId());
  setDirty();
  renderAll();
}

function addIconAt(point) {
  const assetId = elements.markerAssetSelect.value;
  const size = 56;
  mapConfig.markers = mapConfig.markers || [];
  mapConfig.markers.push({
    id: generateId("icono"),
    assetId,
    x: Math.round(point.x - size / 2),
    y: Math.round(point.y - size / 2),
    width: size,
    height: size,
    label: findAsset(config.catalog, assetId)?.name || "Icono"
  });
  pendingIconClick = false;
  elements.addIconButton.classList.remove("active");
  setDirty();
  renderMarkers();
}

function addDecorationAt(point) {
  const assetId = elements.decorationAssetSelect.value;
  const size = 90;

  if (!assetId) {
    return;
  }

  mapConfig.decorations = mapConfig.decorations || [];
  mapConfig.decorations.push({
    id: generateId("decoracion"),
    assetId,
    x: Math.round(point.x - size / 2),
    y: Math.round(point.y - size / 2),
    width: size,
    height: size,
    rotation: 0,
    mirrored: false,
    label: findAsset(config.catalog, assetId)?.name || "Decoracion"
  });
  pendingDecorationClick = false;
  elements.addDecorationButton.classList.remove("active");
  setDirty();
  renderDecorationsLayer();
}

function setTool(tool) {
  activeTool = tool;
  elements.nodeToolButton.classList.toggle("active", tool === "node");
  elements.iconToolButton.classList.toggle("active", tool === "icon");
}

async function handleRouteAssetUpload(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  elements.saveStatus.textContent = "Subiendo asset...";
  const uploaded = await uploadFile(file, "route-asset");
  config.catalog.routeAssets = config.catalog.routeAssets || [];
  config.catalog.routeAssets.push({
    id: generateId("asset"),
    name: uploaded.name,
    type: "single",
    src: uploaded.src
  });
  event.target.value = "";
  setDirty();
  renderSegments();
}

async function handleBackgroundUpload(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  elements.saveStatus.textContent = "Subiendo mapa...";
  const uploaded = await uploadFile(file, "map");
  config.catalog.backgrounds = config.catalog.backgrounds || [];
  config.catalog.backgrounds.push({
    id: generateId("mapa"),
    name: uploaded.name,
    src: uploaded.src
  });
  mapConfig.background = uploaded.src;
  elements.mapImage.src = mapConfig.background;
  event.target.value = "";
  setDirty();
  renderBackgroundControls();
}

async function handleIconUpload(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  elements.saveStatus.textContent = "Subiendo icono...";
  const uploaded = await uploadFile(file, "icon");
  config.catalog.markerIcons = config.catalog.markerIcons || [];
  config.catalog.markerIcons.push({
    id: generateId("icono-asset"),
    name: uploaded.name,
    src: uploaded.src
  });
  event.target.value = "";
  setDirty();
  renderMarkerControls();
}

async function handleDecorationUpload(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  elements.saveStatus.textContent = "Subiendo decoracion...";
  const uploaded = await uploadFile(file, "decoration");
  config.catalog.decorations = config.catalog.decorations || [];
  config.catalog.decorations.push({
    id: generateId("decoracion-asset"),
    name: uploaded.name,
    src: uploaded.src
  });
  event.target.value = "";
  setDirty();
  renderDecorationControls();
}

async function handleAudioUpload(event) {
  const file = event.target.files?.[0];
  const route = activeRoute();
  if (!file || !route) {
    return;
  }

  elements.saveStatus.textContent = "Subiendo audio...";
  const uploaded = await uploadFile(file, "audio");
  config.catalog.audios = config.catalog.audios || [];
  config.catalog.audios.push({
    id: generateId("audio"),
    name: uploaded.name,
    src: uploaded.src
  });
  route.audio = uploaded.src;
  event.target.value = "";
  setDirty();
  renderAudioSelect(route);
}

function updateNodeInput(event) {
  const input = event.target.closest("[data-node-index]");
  if (!input) {
    return;
  }

  const route = activeRoute();
  const node = route?.nodes[Number(input.dataset.nodeIndex)];
  if (!node) {
    return;
  }

  node[input.dataset.axis] = Number(input.value) || 0;
  normalizeSegmentAssets(route, fallbackRouteAssetId());
  setDirty();
  renderRouteGraphics();
  renderNodes();
}

function updateSegmentAsset(event) {
  const select = event.target.closest("[data-segment-index]");
  if (!select) {
    return;
  }

  const route = activeRoute();
  route.segmentAssets[Number(select.dataset.segmentIndex)] = select.value;
  setDirty();
  renderRouteGraphics();
}

function updateSegmentTransform(event) {
  const mirrorButton = event.target.closest("[data-segment-mirror]");
  const rotateButton = event.target.closest("[data-segment-rotate]");
  const route = activeRoute();

  if (!route || (!mirrorButton && !rotateButton)) {
    return;
  }

  normalizeSegmentAssets(route, fallbackRouteAssetId());
  const index = Number((mirrorButton || rotateButton).dataset.segmentMirror ?? (mirrorButton || rotateButton).dataset.segmentRotate);
  route.segmentOptions[index] = route.segmentOptions[index] || { rotation: 0, mirrored: false };

  if (mirrorButton) {
    route.segmentOptions[index].mirrored = !route.segmentOptions[index].mirrored;
  }

  if (rotateButton) {
    route.segmentOptions[index].rotation = rotate45(route.segmentOptions[index].rotation);
  }

  setDirty();
  renderSegments();
  renderRouteGraphics();
}

function updateMarkerField(event) {
  const input = event.target.closest("[data-marker-id]");
  if (!input) {
    return;
  }

  const marker = mapConfig.markers.find((item) => item.id === input.dataset.markerId);
  if (!marker) {
    return;
  }

  if (input.dataset.field === "width") {
    marker.width = Math.max(16, Number(input.value) || 50);
    marker.height = marker.width;
  } else {
    marker[input.dataset.field] = input.value;
  }

  setDirty();
  renderMarkers();
}

function deleteMarkerFromEvent(event) {
  const deleteButton = event.target.closest("[data-delete-marker]");
  const mirrorButton = event.target.closest("[data-marker-mirror]");
  const rotateButton = event.target.closest("[data-marker-rotate]");

  if (deleteButton) {
    mapConfig.markers = mapConfig.markers.filter((marker) => marker.id !== deleteButton.dataset.deleteMarker);
    setDirty();
    renderMarkers();
    renderMarkerControls();
    return;
  }

  const markerId = mirrorButton?.dataset.markerMirror || rotateButton?.dataset.markerRotate;
  const marker = mapConfig.markers.find((item) => item.id === markerId);

  if (!marker) {
    return;
  }

  if (mirrorButton) {
    marker.mirrored = !marker.mirrored;
  }

  if (rotateButton) {
    marker.rotation = rotate45(marker.rotation);
  }

  setDirty();
  renderMarkers();
  renderMarkerControls();
}

function handleDecorationListClick(event) {
  const deleteButton = event.target.closest("[data-delete-decoration]");
  const mirrorButton = event.target.closest("[data-decoration-mirror]");
  const rotateButton = event.target.closest("[data-decoration-rotate]");

  if (deleteButton) {
    mapConfig.decorations = (mapConfig.decorations || []).filter((item) => item.id !== deleteButton.dataset.deleteDecoration);
    setDirty();
    renderDecorationsLayer();
    renderDecorationControls();
    return;
  }

  const decorationId = mirrorButton?.dataset.decorationMirror || rotateButton?.dataset.decorationRotate;
  const decoration = (mapConfig.decorations || []).find((item) => item.id === decorationId);

  if (!decoration) {
    return;
  }

  if (mirrorButton) {
    decoration.mirrored = !decoration.mirrored;
  }

  if (rotateButton) {
    decoration.rotation = rotate45(decoration.rotation);
  }

  setDirty();
  renderDecorationsLayer();
  renderDecorationControls();
}

function updateDecorationField(event) {
  const input = event.target.closest("[data-decoration-id]");
  if (!input) {
    return;
  }

  const decoration = (mapConfig.decorations || []).find((item) => item.id === input.dataset.decorationId);
  if (!decoration) {
    return;
  }

  if (input.dataset.field === "width") {
    decoration.width = Math.max(16, Number(input.value) || 80);
    decoration.height = decoration.width;
  } else {
    decoration[input.dataset.field] = input.value;
  }

  setDirty();
  renderDecorationsLayer();
}

function startDrag(event) {
  const node = event.target.closest(".editor-node");
  const icon = event.target.closest(".editor-icon-handle");
  const decorationHandle = event.target.closest(".editor-decoration-handle");

  if (!node && !icon && !decorationHandle) {
    return;
  }

  const point = getSvgPoint(elements.layer, event);

  if (node) {
    const route = activeRoute();
    const index = Number(node.dataset.index);
    const current = route.nodes[index];
    dragState = {
      type: "node",
      index,
      offsetX: point.x - current.x,
      offsetY: point.y - current.y
    };
  }

  if (decorationHandle) {
    const decoration = (mapConfig.decorations || []).find((item) => item.id === decorationHandle.dataset.decorationId);
    dragState = {
      type: "decoration",
      decorationId: decorationHandle.dataset.decorationId,
      offsetX: point.x - decoration.x,
      offsetY: point.y - decoration.y
    };
  } else if (icon) {
    const marker = mapConfig.markers.find((item) => item.id === icon.dataset.markerId);
    dragState = {
      type: "icon",
      markerId: icon.dataset.markerId,
      offsetX: point.x - marker.x,
      offsetY: point.y - marker.y
    };
  }

  event.target.setPointerCapture(event.pointerId);
  event.preventDefault();
}

function moveDrag(event) {
  if (!dragState) {
    return;
  }

  const point = getSvgPoint(elements.layer, event);

  if (dragState.type === "node") {
    const route = activeRoute();
    route.nodes[dragState.index] = clampPoint({
      x: point.x - dragState.offsetX,
      y: point.y - dragState.offsetY
    });
    normalizeSegmentAssets(route, fallbackRouteAssetId());
    renderRouteGraphics();
    renderNodes();
  }

  if (dragState.type === "icon") {
    const marker = mapConfig.markers.find((item) => item.id === dragState.markerId);
    marker.x = Math.round(point.x - dragState.offsetX);
    marker.y = Math.round(point.y - dragState.offsetY);
    renderMarkers();
  }

  if (dragState.type === "decoration") {
    const decoration = (mapConfig.decorations || []).find((item) => item.id === dragState.decorationId);
    decoration.x = Math.round(point.x - dragState.offsetX);
    decoration.y = Math.round(point.y - dragState.offsetY);
    renderDecorationsLayer();
  }

  setDirty();
}

function endDrag() {
  dragState = null;
}

async function saveAll() {
  elements.saveButton.disabled = true;
  elements.saveStatus.textContent = "Guardando...";

  try {
    await saveRouteConfig(config);
    setSaved();
  } catch (error) {
    elements.saveStatus.textContent = error.message;
    elements.saveStatus.classList.add("dirty");
  } finally {
    elements.saveButton.disabled = false;
  }
}

async function init() {
  config = await loadRouteConfig();
  mapConfig = config.maps[mapKey];

  elements.backLink.href = mapHome;
  elements.editorTitle.textContent = mapKey === "mapar" ? "Configurar MapaR" : "Configurar Terminal";
  elements.mapImage.src = mapConfig.background;
  elements.layer.setAttribute("viewBox", mapConfig.viewBox);
  activeRouteId = mapConfig.routes[0]?.id || "";

  elements.routeNameInput.addEventListener("input", syncActiveRouteFromInputs);
  elements.routeColorInput.addEventListener("input", syncActiveRouteFromInputs);
  elements.routeInstructionsInput.addEventListener("input", syncActiveRouteFromInputs);
  elements.routeAudioSelect.addEventListener("change", syncRouteAudio);
  elements.routeAssetSizeInput.addEventListener("input", syncRouteAssetSize);
  elements.routeAssetUploadInput.addEventListener("change", (event) => {
    handleRouteAssetUpload(event).catch((error) => {
      elements.saveStatus.textContent = error.message;
      elements.saveStatus.classList.add("dirty");
    });
  });
  elements.backgroundSelect.addEventListener("change", () => {
    mapConfig.background = elements.backgroundSelect.value;
    elements.mapImage.src = mapConfig.background;
    setDirty();
  });
  elements.backgroundUploadInput.addEventListener("change", (event) => {
    handleBackgroundUpload(event).catch((error) => {
      elements.saveStatus.textContent = error.message;
      elements.saveStatus.classList.add("dirty");
    });
  });
  elements.iconUploadInput.addEventListener("change", (event) => {
    handleIconUpload(event).catch((error) => {
      elements.saveStatus.textContent = error.message;
      elements.saveStatus.classList.add("dirty");
    });
  });
  elements.decorationUploadInput.addEventListener("change", (event) => {
    handleDecorationUpload(event).catch((error) => {
      elements.saveStatus.textContent = error.message;
      elements.saveStatus.classList.add("dirty");
    });
  });
  elements.audioUploadInput.addEventListener("change", (event) => {
    handleAudioUpload(event).catch((error) => {
      elements.saveStatus.textContent = error.message;
      elements.saveStatus.classList.add("dirty");
    });
  });
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });
  elements.newRouteButton.addEventListener("click", addRoute);
  elements.duplicateRouteButton.addEventListener("click", duplicateRoute);
  elements.deleteRouteButton.addEventListener("click", deleteActiveRoute);
  elements.archiveRouteButton.addEventListener("click", () => {
    const route = activeRoute();
    route.archived = !route.archived;
    setDirty();
    renderAll();
  });
  elements.addNodeButton.addEventListener("click", () => {
    pendingNodeClick = true;
    pendingIconClick = false;
    pendingDecorationClick = false;
    setTool("node");
    elements.addNodeButton.classList.add("active");
    elements.addIconButton.classList.remove("active");
    elements.addDecorationButton.classList.remove("active");
  });
  elements.deleteNodeButton.addEventListener("click", deleteLastNode);
  elements.addIconButton.addEventListener("click", () => {
    pendingIconClick = true;
    pendingNodeClick = false;
    pendingDecorationClick = false;
    setTool("icon");
    elements.addIconButton.classList.add("active");
    elements.addNodeButton.classList.remove("active");
    elements.addDecorationButton.classList.remove("active");
  });
  elements.addDecorationButton.addEventListener("click", () => {
    pendingDecorationClick = true;
    pendingIconClick = false;
    pendingNodeClick = false;
    setTool("icon");
    elements.addDecorationButton.classList.add("active");
    elements.addIconButton.classList.remove("active");
    elements.addNodeButton.classList.remove("active");
  });
  elements.nodeToolButton.addEventListener("click", () => setTool("node"));
  elements.iconToolButton.addEventListener("click", () => setTool("icon"));
  elements.saveButton.addEventListener("click", saveAll);
  elements.nodeList.addEventListener("change", updateNodeInput);
  elements.segmentAssetList.addEventListener("change", updateSegmentAsset);
  elements.segmentAssetList.addEventListener("click", updateSegmentTransform);
  elements.markerList.addEventListener("change", updateMarkerField);
  elements.markerList.addEventListener("click", deleteMarkerFromEvent);
  elements.decorationList.addEventListener("change", updateDecorationField);
  elements.decorationList.addEventListener("click", handleDecorationListClick);
  elements.layer.addEventListener("pointerdown", startDrag);
  elements.layer.addEventListener("pointermove", moveDrag);
  elements.layer.addEventListener("pointerup", endDrag);
  elements.layer.addEventListener("pointercancel", endDrag);
  elements.layer.addEventListener("click", (event) => {
    if (dragState || event.target.closest(".editor-node, .editor-icon-handle")) {
      return;
    }

    const point = clampPoint(getSvgPoint(elements.layer, event));

    if (pendingNodeClick && activeTool === "node") {
      addNodeAt(point);
    }

    if (pendingIconClick && activeTool === "icon") {
      addIconAt(point);
    }

    if (pendingDecorationClick && activeTool === "icon") {
      addDecorationAt(point);
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (!hasUnsavedChanges) {
      return;
    }

    event.preventDefault();
    event.returnValue = "";
  });

  renderAll();
  setMode(activeMode);
}

init().catch((error) => {
  document.body.innerHTML = `<main class="terminal-error">${error.message}</main>`;
});
