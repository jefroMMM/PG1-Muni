import { createPlacedItemsEditor } from "./editor/placed-items-editor.js";
import { bindCatalogUploads } from "./editor/catalog-uploads.js";
import { createInstructionEditor } from "./editor/instruction-editor.js";
import { createAreaEditor } from "./editor/area-editor.js";
import { createPreviewController } from "./editor/preview-controller.js";
import { loadRouteConfig, saveRouteConfig, saveEditorScope } from "./shared/config-api.js";
import { getInstructionSteps } from "./shared/instructions.js";
import { getRouteTiming } from "./shared/route-timing.js";
import { serializeHighlight } from "./shared/highlight-area.js";
import { getMapKey, getMapLinks } from "./shared/sections.js";
import { filterResources, renderResourceOptions } from "./shared/resource-catalog.js";
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

const mapKey = getMapKey();
const mapHome = getMapLinks(mapKey).home;
const editorParams = new URLSearchParams(window.location.search);
const editorScope = editorParams.get("scope");
let selectedRouteId = editorParams.get("route");
let isNewRoute = editorScope === "route" && editorParams.get("new") === "1";
const isRouteEditor = editorScope === "route";
const isMapEditor = editorScope === "map";
const isScopedEditor = isRouteEditor || isMapEditor;
const allowedModes = isRouteEditor
  ? ["nodes", "assets", "area", "text-audio"]
  : isMapEditor ? ["map", "icons", "decorations"] : null;

const elements = {
  backLink: document.getElementById("backLink"),
  editorTitle: document.getElementById("editorTitle"),
  saveStatus: document.getElementById("saveStatus"),
  routeInspector: document.getElementById("routeInspector"),
  mapImage: document.getElementById("editorMapImage"),
  layer: document.getElementById("editorLayer"),
  highlightLayer: document.getElementById("editorHighlightLayer"),
  areaHandles: document.getElementById("editorAreaHandles"),
  drawAreaButton: document.getElementById("drawAreaButton"),
  cancelAreaButton: document.getElementById("cancelAreaButton"),
  removeAreaButton: document.getElementById("removeAreaButton"),
  areaStatus: document.getElementById("areaStatus"),
  areaPointList: document.getElementById("areaPointList"),
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
  routeDurationInput: document.getElementById("routeDurationInput"),
  instructionStepList: document.getElementById("instructionStepList"),
  addInstructionStepButton: document.getElementById("addInstructionStepButton"),
  routeAudioSelect: document.getElementById("routeAudioSelect"),
  audioScope: document.getElementById("audioScope"),
  routeAssetScope: document.getElementById("routeAssetScope"),
  markerScope: document.getElementById("markerScope"),
  decorationScope: document.getElementById("decorationScope"),
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
createPreviewController({ getConfig: () => config, getRoute: activeRoute, mapKey });

let config;
let mapConfig;
let activeRouteId = "";
let activeTool = "node";
let activeMode = "routes";
let pendingNodeClick = false;
let pendingIconClick = false;
let pendingDecorationClick = false;
let dragState = null;
let dragFrame = null;
let latestDragEvent = null;
let hasUnsavedChanges = false;
const instructionEditor = createInstructionEditor({
  list: elements.instructionStepList,
  addButton: elements.addInstructionStepButton,
  getRoute: activeRoute,
  onChange: syncActiveRouteFromInputs
});
const areaEditor = createAreaEditor({
  elements, getRoute: activeRoute, getMode: () => activeMode,
  onChange: setDirty, redraw: renderRouteGraphics,
  onStart: () => { pendingNodeClick = pendingIconClick = pendingDecorationClick = false; }
});

const markerEditor = createPlacedItemsEditor({
  mapKey, getMaps: () => config.maps, scopeSelect: elements.markerScope,
  getMap: () => mapConfig, getCatalog: () => config.catalog,
  group: "markers", catalogGroup: "markerIcons", kind: "marker",
  select: elements.markerAssetSelect, list: elements.markerList,
  defaultSize: 50, maxSize: 180, onChange: setDirty, renderGraphics: renderMarkers
});
const decorationEditor = createPlacedItemsEditor({
  mapKey, getMaps: () => config.maps, scopeSelect: elements.decorationScope,
  getMap: () => mapConfig, getCatalog: () => config.catalog,
  group: "decorations", catalogGroup: "decorations", kind: "decoration",
  select: elements.decorationAssetSelect, list: elements.decorationList,
  defaultSize: 80, maxSize: 260, onChange: setDirty, renderGraphics: renderDecorationsLayer
});

function activeRoute() {
  if (isMapEditor) return undefined;
  if (isRouteEditor) return mapConfig.routes.find((route) => route.id === selectedRouteId);
  return mapConfig.routes.find((route) => route.id === activeRouteId) || mapConfig.routes[0];
}

function fallbackRouteAssetId() {
  return mapConfig.routeStyle === "assets-only" ? "mapr-footprints-auto" : "footprints-auto";
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

function syncActiveRouteFromInputs() {
  const route = activeRoute();
  if (!route) {
    return;
  }

  route.name = elements.routeNameInput.value.trim();
  route.buttonColor = elements.routeColorInput.value || "#147a69";
  route.instructionSteps = instructionEditor.read().map((value) => value.trim());
  route.instructions = route.instructionSteps.filter(Boolean).join("\n");
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
  if (allowedModes && !allowedModes.includes(mode)) return;
  areaEditor.cancel(false);
  activeMode = mode;
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== mode;
  });
  renderRouteGraphics();
}

function renderRouteList() {
  const routes = isMapEditor ? [] : isRouteEditor ? [activeRoute()] : mapConfig.routes;
  const items = routes.filter(Boolean).map((route) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `route-list-item ${route.id === activeRouteId ? "active" : ""}`;
    const name = document.createElement("span");
    name.textContent = route.name;
    const status = document.createElement("small");
    status.textContent = route.archived ? "Archivada" : "Visible";
    button.append(name, status);
    button.addEventListener("click", () => {
      areaEditor.cancel(false);
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
  if (isMapEditor) {
    elements.routeInspector.replaceChildren();
    const message = document.createElement("strong");
    message.textContent = "Configuración del mapa: imagen de fondo, iconos y decoraciones";
    elements.routeInspector.append(message);
    return;
  }
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
    <strong></strong>
    <span>${route.archived ? "Archivada" : "Visible"}</span>
    <span>${nodes.length} nodos</span>
    <span>${segmentCount} tramos</span>
    <span>${Math.round(routeLength(nodes))} px</span>
    <span>${route.audio ? "Con audio" : "Sin audio"}</span>
    ${warnings.length ? `<em>${warnings.join(" · ")}</em>` : "<em>Lista para usar</em>"}
  `;
  elements.routeInspector.querySelector("strong").textContent = route.name || "Ruta sin nombre";
}

function renderForm() {
  const route = activeRoute();
  const hasRoute = Boolean(route);
  elements.routeDurationInput.disabled = !hasRoute;
  elements.routeDurationInput.value = route ? getRouteTiming(route, mapConfig).total / 1000 : "";

  [elements.routeNameInput, elements.routeColorInput, elements.addInstructionStepButton, elements.routeAudioSelect, elements.routeAssetSizeInput, elements.archiveRouteButton, elements.duplicateRouteButton, elements.deleteRouteButton, elements.addNodeButton, elements.deleteNodeButton]
    .forEach((control) => {
      control.disabled = !hasRoute;
    });

  if (!route) {
    elements.routeNameInput.value = "";
    elements.routeColorInput.value = "#147a69";
    elements.instructionStepList.replaceChildren();
    elements.routeAssetSizeInput.value = mapConfig.routeAssetSize;
    return;
  }

  normalizeSegmentAssets(route, fallbackRouteAssetId());
  elements.routeNameInput.value = route.name || "";
  elements.routeColorInput.value = route.buttonColor || "#147a69";
  instructionEditor.render(route.instructionSteps || getInstructionSteps(route));
  elements.routeAssetSizeInput.value = route.assetSize || mapConfig.routeAssetSize;
  elements.archiveRouteButton.textContent = route.archived ? "Desarchivar" : "Archivar";
  renderAudioSelect(route);
}

function renderAudioSelect(route) {
  if (!route) return;
  const currentAudio = route.audio || "";
  const options = filterResources(config.catalog.audios || [], mapKey, elements.audioScope.value, [currentAudio], "src");

  if (currentAudio && !options.some((audio) => audio.src === currentAudio)) {
    options.push({ name: "Audio actual", src: currentAudio });
  }

  renderResourceOptions(elements.routeAudioSelect, options, {
    maps: config.maps, mapKey, scope: elements.audioScope.value, value: currentAudio, valueField: "src", emptyLabel: "Sin audio"
  });
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
  const rows = segments.map((assetId, index) => {
    const row = document.createElement("div");
    row.className = "asset-row";
    const label = document.createElement("label");
    label.className = "field-label compact-field asset-select-field";
    const select = document.createElement("select");
    select.dataset.segmentIndex = String(index);

    const assets = filterResources(config.catalog.routeAssets || [], mapKey, elements.routeAssetScope.value, [assetId]);
    renderResourceOptions(select, assets, { maps: config.maps, mapKey, scope: elements.routeAssetScope.value, value: assetId });

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
  areaEditor.render();

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
  if (areaEditor.draft?.length) {
    elements.highlightLayer.replaceChildren(createSvgElement("polyline", {
      class: "area-draft", points: serializeHighlight(areaEditor.draft)
    }));
  }
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
  const handles = (isRouteEditor ? [] : mapConfig.markers || []).map((marker) => {
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
  const handles = (isRouteEditor ? [] : mapConfig.decorations || []).map((decoration) => createSvgElement("rect", {
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
}

function renderDecorationsLayer() {
  renderDecorations({
    parent: elements.decorationLayer,
    catalog: config.catalog,
    decorations: mapConfig.decorations || []
  });
  renderPlacedDecorationHandles();
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
  markerEditor.renderControls();
  decorationEditor.renderControls();
  renderBackgroundControls();
}

function addRoute() {
  if (isScopedEditor) return;
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
  if (isScopedEditor) return;
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
  if (isScopedEditor) return;
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
  markerEditor.renderControls();
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
  decorationEditor.renderControls();
}

function setTool(tool) {
  activeTool = tool;
  elements.nodeToolButton.classList.toggle("active", tool === "node");
  elements.iconToolButton.classList.toggle("active", tool === "icon");
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

  const point = clampPoint({ ...node, [input.dataset.axis]: Number(input.value) || 0 });
  Object.assign(node, point);
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

function startDrag(event) {
  if (activeMode === "area") {
    const handle = event.target.closest(".editor-area-handle");
    if (!handle || areaEditor.draft !== null) return;
    dragState = { type: "area", index: Number(handle.dataset.index) };
    elements.layer.setPointerCapture(event.pointerId);
    event.preventDefault();
    return;
  }
  const node = event.target.closest(".editor-node");
  const icon = event.target.closest(".editor-icon-handle");
  const decorationHandle = event.target.closest(".editor-decoration-handle");

  if (!node && !icon && !decorationHandle) {
    return;
  }
  if ((isRouteEditor && !node) || (isMapEditor && node)) return;

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

  elements.layer.setPointerCapture(event.pointerId);
  event.preventDefault();
}

function moveDrag(event) {
  if (!dragState) {
    return;
  }

  const point = getSvgPoint(elements.layer, event);

  if (dragState.type === "area") {
    areaEditor.updatePoint(dragState.index, clampPoint(point));
    return;
  }

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

function queueDragMove(event) {
  if (!dragState) return;
  latestDragEvent = event;
  if (dragFrame !== null) return;
  dragFrame = requestAnimationFrame(() => {
    dragFrame = null;
    const next = latestDragEvent;
    latestDragEvent = null;
    if (next) moveDrag(next);
  });
}

function endDrag() {
  if (dragFrame !== null) cancelAnimationFrame(dragFrame);
  dragFrame = null;
  if (latestDragEvent) moveDrag(latestDragEvent);
  latestDragEvent = null;
  dragState = null;
}

async function saveAll() {
  if (areaEditor.draft !== null) {
    elements.areaStatus.textContent = "Completa los cuatro puntos o cancela el marcado antes de guardar.";
    return;
  }
  if (!elements.routeDurationInput.disabled && !elements.routeDurationInput.checkValidity()) {
    setMode("text-audio");
    elements.routeDurationInput.reportValidity();
    return;
  }
  elements.saveButton.disabled = true;
  elements.saveStatus.textContent = "Guardando...";

  try {
    if (isRouteEditor) {
      await saveEditorScope(mapKey, selectedRouteId, {
        route: activeRoute(),
        catalog: { routeAssets: config.catalog.routeAssets, audios: config.catalog.audios }
      }, isNewRoute);
      if (isNewRoute) {
        isNewRoute = false;
        const url = new URL(window.location.href);
        url.searchParams.delete("new");
        url.searchParams.set("route", selectedRouteId);
        window.history.replaceState(null, "", url);
      }
    } else if (isMapEditor) {
      await saveEditorScope(mapKey, null, {
        map: { background: mapConfig.background, markers: mapConfig.markers, decorations: mapConfig.decorations },
        catalog: { backgrounds: config.catalog.backgrounds, markerIcons: config.catalog.markerIcons, decorations: config.catalog.decorations }
      });
    } else {
      await saveRouteConfig(config);
    }
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
  if (!mapConfig) throw new Error("La sección seleccionada ya no existe.");
  if (isNewRoute) {
    selectedRouteId = generateId("ruta");
    mapConfig.routes.push({ id: selectedRouteId, name: "Nueva ruta", archived: false, buttonColor: "#147a69", instructions: "", audio: "", assetSize: mapConfig.routeAssetSize, nodes: [{ x: 1000, y: 700 }, { x: 1100, y: 700 }], segmentAssets: [fallbackRouteAssetId()], segmentOptions: [{ rotation: 0, mirrored: false }] });
    setDirty();
  }

  if (isRouteEditor && !activeRoute()) throw new Error("La ruta seleccionada ya no existe. Vuelve al dashboard.");
  elements.backLink.href = isScopedEditor
    ? editorParams.get("dashboard") === "2" ? "/dashboard2" : "/dashboard"
    : mapHome;
  const dashboardView = editorParams.get("dashboardView");
  if (isScopedEditor && editorParams.get("dashboard") === "2" && Object.hasOwn(config.maps, dashboardView)) {
    elements.backLink.href += `#${encodeURIComponent(dashboardView)}`;
  }
  elements.backLink.textContent = isScopedEditor ? "Volver al dashboard" : "Volver al mapa";
  const mapLabel = mapConfig.sectionName || (mapKey === "mapar" ? "MapaR" : "Mapa");
  elements.editorTitle.textContent = isRouteEditor ? `${mapLabel} · ${activeRoute().name}` : `Configurar ${mapLabel}`;
  document.title = elements.editorTitle.textContent;
  elements.mapImage.src = mapConfig.background;
  elements.layer.setAttribute("viewBox", mapConfig.viewBox);
  activeRouteId = isRouteEditor ? selectedRouteId : mapConfig.routes[0]?.id || "";
  document.getElementById("previewButton").hidden = isMapEditor;
  if (isScopedEditor) {
    activeMode = isRouteEditor ? "text-audio" : "map";
    document.querySelector(".section-heading h1").textContent = isRouteEditor ? "Editar esta ruta" : "Editar este mapa";
    document.querySelectorAll("[data-mode]").forEach((button) => { button.hidden = !allowedModes.includes(button.dataset.mode); });
    document.querySelector('[data-panel="routes"]').hidden = true;
    elements.newRouteButton.hidden = true;
    elements.duplicateRouteButton.hidden = true;
    elements.deleteRouteButton.hidden = true;
    elements.nodeToolButton.hidden = isMapEditor;
    elements.iconToolButton.hidden = isRouteEditor;
    if (isRouteEditor) {
      const statusSection = document.createElement("section");
      statusSection.className = "panel-section";
      statusSection.append(elements.archiveRouteButton);
      document.querySelector(".config-panel").append(statusSection);
    } else { setTool("icon"); }
  }

  elements.routeNameInput.addEventListener("input", syncActiveRouteFromInputs);
  elements.routeColorInput.addEventListener("input", syncActiveRouteFromInputs);
  elements.routeDurationInput.addEventListener("input", () => {
    const route = activeRoute();
    if (!route) return;
    setDirty();
    if (elements.routeDurationInput.checkValidity()) {
      route.durationSeconds = elements.routeDurationInput.valueAsNumber;
    }
  });
  elements.routeAudioSelect.addEventListener("change", syncRouteAudio);
  elements.audioScope.addEventListener("change", () => renderAudioSelect(activeRoute()));
  elements.routeAssetScope.addEventListener("change", renderSegments);
  elements.routeAssetSizeInput.addEventListener("input", syncRouteAssetSize);
  elements.backgroundSelect.addEventListener("change", () => {
    mapConfig.background = elements.backgroundSelect.value;
    elements.mapImage.src = mapConfig.background;
    setDirty();
  });
  bindCatalogUploads({
    elements, mapKey, getCatalog: () => config.catalog, getMap: () => mapConfig,
    getRoute: activeRoute, onChange: setDirty,
    renderers: { segments: renderSegments, background: renderBackgroundControls,
      markers: markerEditor.renderControls, decorations: decorationEditor.renderControls, audio: renderAudioSelect }
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
  elements.layer.addEventListener("pointerdown", startDrag);
  elements.layer.addEventListener("pointermove", queueDragMove);
  elements.layer.addEventListener("pointerup", endDrag);
  elements.layer.addEventListener("pointercancel", endDrag);
  elements.layer.addEventListener("click", (event) => {
    if (activeMode === "area") { areaEditor.handleClick(event); return; }
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
  const message = document.createElement("main");
  message.className = "terminal-error";
  message.textContent = error.message;
  document.body.replaceChildren(message);
});
