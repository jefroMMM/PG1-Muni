export const svgNamespace = "http://www.w3.org/2000/svg";

export function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(svgNamespace, tagName);

  Object.entries(attributes).forEach(([name, value]) => {
    if (value === undefined || value === null) {
      return;
    }

    if (name === "xlink:href") {
      element.setAttributeNS("http://www.w3.org/1999/xlink", name, value);
      return;
    }

    element.setAttribute(name, value);
  });

  return element;
}

export function getSvgPoint(svg, event) {
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(svg.getScreenCTM().inverse());
}

export function clampPoint(point) {
  return {
    x: Math.max(0, Math.min(2000, Math.round(point.x))),
    y: Math.max(0, Math.min(1000, Math.round(point.y)))
  };
}

export function getSegmentDirection(start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;

  if (Math.abs(dx) >= Math.abs(dy)) {
    return dx >= 0 ? "right" : "left";
  }

  return dy >= 0 ? "down" : "up";
}

export function routePathFromNodes(nodes = []) {
  return nodes
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
}

export function findAsset(catalog, assetId) {
  for (const group of ["routeAssets", "markerIcons", "decorations", "backgrounds"]) {
    const asset = catalog[group]?.find((asset) => asset.id === assetId);
    if (asset) return asset;
  }
}

export function resolveRouteAsset(catalog, assetId, start, end, index) {
  const asset = (index ? index.get(assetId) : findAsset(catalog, assetId)) || catalog.routeAssets?.[0];

  if (!asset) {
    return "";
  }

  if (asset.type === "directional") {
    const direction = getSegmentDirection(start, end);
    return asset.directions?.[direction] || Object.values(asset.directions || {})[0] || "";
  }

  return asset.src || "";
}

export function normalizeSegmentAssets(route, fallbackAssetId) {
  const segmentCount = Math.max(0, (route.nodes || []).length - 1);
  route.segmentAssets = Array.from({ length: segmentCount }, (_, index) => (
    route.segmentAssets?.[index] || fallbackAssetId
  ));
  route.segmentOptions = Array.from({ length: segmentCount }, (_, index) => ({
    rotation: Number(route.segmentOptions?.[index]?.rotation) || 0,
    mirrored: Boolean(route.segmentOptions?.[index]?.mirrored)
  }));
}

export function transformAroundCenter({ x, y, width, height, rotation = 0, mirrored = false }) {
  const centerX = x + width / 2;
  const centerY = y + height / 2;
  const scaleX = mirrored ? -1 : 1;
  return `translate(${centerX} ${centerY}) rotate(${rotation}) scale(${scaleX} 1) translate(${-centerX} ${-centerY})`;
}

export function renderFootprints({ parent, catalog, route, assetSize, stepDistance, revealTime, className }) {
  const nodes = route.nodes || [];
  const footprints = [];
  const assetIndex = new Map();
  for (const group of ["routeAssets", "markerIcons", "decorations", "backgrounds"]) {
    for (const asset of catalog[group] || []) {
      if (!assetIndex.has(asset.id)) assetIndex.set(asset.id, asset);
    }
  }
  const spacing = Math.max(1, Number(stepDistance) || 30);

  for (let index = 0; index < nodes.length - 1; index += 1) {
    const start = nodes[index];
    const end = nodes[index + 1];
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    const steps = Math.max(1, Math.floor(length / spacing));
    const sprite = resolveRouteAsset(catalog, route.segmentAssets?.[index], start, end, assetIndex);

    for (let step = 1; step <= steps; step += 1) {
      const ratio = step / (steps + 1);
      const x = start.x + dx * ratio;
      const y = start.y + dy * ratio;
      const imageX = Math.round(x - assetSize / 2);
      const imageY = Math.round(y - assetSize / 2);
      const options = route.segmentOptions?.[index] || {};
      footprints.push(createSvgElement("image", {
        class: className,
        href: sprite,
        "xlink:href": sprite,
        x: imageX,
        y: imageY,
        width: assetSize,
        height: assetSize,
        transform: transformAroundCenter({
          x: imageX,
          y: imageY,
          width: assetSize,
          height: assetSize,
          rotation: options.rotation,
          mirrored: options.mirrored
        }),
        preserveAspectRatio: "xMidYMid meet"
      }));
    }
  }

  footprints.forEach((footprint, index) => {
    const delay = footprints.length <= 1 ? 0 : (revealTime / (footprints.length - 1)) * index;
    footprint.style.animationDelay = `${Math.round(delay)}ms`;
  });

  parent.replaceChildren(...footprints);
}

export function renderMapMarkers({ parent, catalog, markers = [], className = "map-logo-marker" }) {
  const markerAssets = catalog.markerIcons || [];
  const elements = markers.map((marker) => {
    const asset = markerAssets.find((item) => item.id === marker.assetId);
    return createSvgElement("image", {
      class: className,
      href: asset?.src || "",
      "xlink:href": asset?.src || "",
      x: marker.x,
      y: marker.y,
      width: marker.width || 50,
      height: marker.height || 50,
      transform: transformAroundCenter({
        x: marker.x,
        y: marker.y,
        width: marker.width || 50,
        height: marker.height || 50,
        rotation: marker.rotation,
        mirrored: marker.mirrored
      }),
      "aria-label": marker.label || "",
      preserveAspectRatio: "xMidYMid meet"
    });
  });

  parent.replaceChildren(...elements);
}

export function renderDecorations({ parent, catalog, decorations = [], className = "map-decoration" }) {
  const elements = decorations.map((decoration) => {
    const asset = findAsset(catalog, decoration.assetId);
    const width = decoration.width || 80;
    const height = decoration.height || width;
    return createSvgElement("image", {
      class: className,
      href: asset?.src || "",
      "xlink:href": asset?.src || "",
      x: decoration.x,
      y: decoration.y,
      width,
      height,
      transform: transformAroundCenter({
        x: decoration.x,
        y: decoration.y,
        width,
        height,
        rotation: decoration.rotation,
        mirrored: decoration.mirrored
      }),
      "aria-label": decoration.label || "",
      preserveAspectRatio: "xMidYMid meet"
    });
  });

  parent.replaceChildren(...elements);
}

export function generateId(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}
