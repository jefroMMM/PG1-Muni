import { parseHighlight, serializeHighlight, validHighlight } from "../shared/highlight-area.js";
import { createSvgElement, clampPoint, getSvgPoint } from "../shared/map-utils.js";

export function createAreaEditor({ elements, getRoute, getMode, onChange, redraw, onStart }) {
  let draft = null;
  const cancel = (refresh = true) => { draft = null; if (refresh) redraw(); };

  function render() {
    const route = getRoute();
    const points = draft ?? parseHighlight(route?.highlightPolygon);
    elements.drawAreaButton.disabled = !route;
    elements.removeAreaButton.disabled = !route?.highlightPolygon;
    elements.cancelAreaButton.hidden = draft === null;
    elements.drawAreaButton.disabled = !route || draft !== null;
    elements.areaStatus.textContent = draft !== null ? `Punto ${draft.length + 1} de 4` : points.length ? "Área de destino definida" : "Sin área de destino";
    elements.areaHandles.replaceChildren();
    elements.areaPointList.replaceChildren();
    if (getMode() !== "area") return;
    points.forEach((point, index) => {
      const handle = createSvgElement("g", { class: "editor-area-handle", "data-index": index, tabindex: "0", role: "button", "aria-label": `Esquina ${index + 1}`, transform: `translate(${point.x} ${point.y})` });
      const text = createSvgElement("text", { "text-anchor": "middle", y: 5 });
      text.textContent = index + 1;
      handle.append(createSvgElement("circle", { r: 15 }), text);
      handle.addEventListener("keydown", (event) => {
        const delta = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
        if (!delta || draft !== null) return;
        event.preventDefault();
        updateAreaPoint(index, clampPoint({ x: point.x + delta[0] * (event.shiftKey ? 10 : 1), y: point.y + delta[1] * (event.shiftKey ? 10 : 1) }));
        elements.areaHandles.children[index]?.focus();
      });
      elements.areaHandles.append(handle);
      if (draft !== null) return;
      const row = document.createElement("div");
      row.className = "area-point-row";
      const title = document.createElement("strong");
      title.textContent = `Esquina ${index + 1}`;
      row.append(title);
      for (const [axis, max] of [["x", 2000], ["y", 1000]]) {
        const label = document.createElement("label");
        label.className = "field-label";
        label.textContent = axis.toUpperCase();
        const input = document.createElement("input");
        input.type = "number";
        input.min = 0;
        input.max = max;
        input.step = 1;
        input.required = true;
        input.value = point[axis];
        input.setAttribute("aria-label", `Esquina ${index + 1}, ${axis.toUpperCase()}`);
        input.addEventListener("change", () => {
          if (input.reportValidity()) updateAreaPoint(index, { ...point, [axis]: input.valueAsNumber });
        });
        label.append(input);
        row.append(label);
      }
      elements.areaPointList.append(row);
    });
  }

  function updateAreaPoint(index, point) {
    const route = getRoute();
    if (!route) return;
    const points = parseHighlight(route.highlightPolygon);
    points[index] = point;
    if (!validHighlight(points)) {
      elements.areaStatus.textContent = "Las esquinas deben formar un área sin cruces.";
      return;
    }
    route.highlightPolygon = serializeHighlight(points);
    onChange();
    redraw();
  }

  elements.drawAreaButton.addEventListener("click", () => {
    if (!getRoute()) return;
    onStart();
    draft = [];
    redraw();
  });
  elements.cancelAreaButton.addEventListener("click", () => cancel());
  elements.removeAreaButton.addEventListener("click", () => {
    if (!getRoute()) return;
    draft = null;
    getRoute().highlightPolygon = "";
    onChange();
    redraw();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && draft !== null) cancel();
  });

  function handleClick(event) {
    if (draft === null || event.target.closest(".editor-area-handle")) return;
    const points = [...draft, clampPoint(getSvgPoint(elements.layer, event))];
    if (points.length === 4) {
      if (!validHighlight(points)) {
        elements.areaStatus.textContent = "Área inválida: marca la cuarta esquina sin cruzar los lados.";
        return;
      }
      getRoute().highlightPolygon = serializeHighlight(points);
      draft = null;
      onChange();
    } else { draft = points; }
    redraw();
  }
  return { render, cancel, updatePoint: updateAreaPoint, handleClick, get draft() { return draft; } };
}
