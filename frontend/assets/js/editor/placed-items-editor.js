import { filterResources, renderResourceOptions } from "../shared/resource-catalog.js";

export function createPlacedItemsEditor({ getMap, getMaps, mapKey, scopeSelect, getCatalog, group, catalogGroup, select, list, kind, maxSize, defaultSize, onChange, renderGraphics }) {
  const idField = `${kind}Id`;
  const items = () => getMap()[group] || [];
  function renderControls() {
    const entries = filterResources(getCatalog()[catalogGroup] || [], mapKey, scopeSelect.value);
    renderResourceOptions(select, entries, { maps: getMaps(), mapKey, scope: scopeSelect.value });
    const assets = new Map((getCatalog()[catalogGroup] || []).map((asset) => [asset.id, asset]));
    list.replaceChildren(...items().map((item) => {
      const row = document.createElement("div");
      row.className = `marker-row${kind === "decoration" ? " decoration-row" : ""}`;
      const image = document.createElement("img");
      image.src = assets.get(item.assetId)?.src || "";
      image.alt = "";
      row.append(image);
      for (const field of ["label", "width"]) {
        const input = document.createElement("input");
        input.type = field === "width" ? "number" : "text";
        input.value = field === "width" ? item.width || defaultSize : item.label || "";
        input.dataset[idField] = item.id;
        input.dataset.field = field;
        input.setAttribute("aria-label", field === "width" ? "Tamaño" : "Nombre");
        if (field === "width") { input.min = 16; input.max = maxSize; }
        row.append(input);
      }
      for (const [action, text] of [["mirror", item.mirrored ? "Sin espejo" : "Espejo"], ["rotate", `${Number(item.rotation) || 0} deg`], ["delete", "Borrar"]]) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = text;
        button.dataset.itemAction = action;
        button.dataset[idField] = item.id;
        row.append(button);
      }
      return row;
    }));
  }
  scopeSelect.addEventListener("change", renderControls);
  list.addEventListener("change", (event) => {
    const input = event.target.closest("input[data-field]");
    const item = input && items().find((item) => item.id === input.dataset[idField]);
    if (!item || !input.reportValidity()) return;
    if (input.dataset.field === "width") {
      item.width = item.height = Number(input.value) || defaultSize;
    } else { item.label = input.value; }
    onChange();
    renderGraphics();
  });
  list.addEventListener("click", (event) => {
    const button = event.target.closest("[data-item-action]");
    const item = button && items().find((item) => item.id === button.dataset[idField]);
    if (!item) return;
    if (button.dataset.itemAction === "delete") getMap()[group] = items().filter((candidate) => candidate !== item);
    if (button.dataset.itemAction === "mirror") item.mirrored = !item.mirrored;
    if (button.dataset.itemAction === "rotate") item.rotation = ((Number(item.rotation) || 0) + 45) % 360;
    onChange();
    renderGraphics();
    renderControls();
  });
  return { renderControls };
}
