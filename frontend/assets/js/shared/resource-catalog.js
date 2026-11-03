export function sectionResourceLabel(sectionId, maps = {}) {
  if (!sectionId || sectionId === "shared") return "Compartidos";
  if (sectionId === "terminal") return "Mapa";
  if (sectionId === "mapar") return "MapaR";
  return maps[sectionId]?.sectionName || maps[sectionId]?.title || sectionId;
}

export function filterResources(entries, mapKey, scope = "section", selected = [], valueField = "id") {
  const current = new Set(selected);
  return entries.filter((asset) => scope === "all" || !asset.sectionId || asset.sectionId === "shared"
    || asset.sectionId === mapKey || current.has(asset[valueField]));
}

export function renderResourceOptions(select, entries, { maps, mapKey, scope = "all", value = "", valueField = "id", emptyLabel } = {}) {
  const previous = value || select.value;
  const groups = new Map();
  const children = [];
  if (emptyLabel) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = emptyLabel;
    children.push(option);
  }
  for (const asset of entries) {
    const sectionId = asset.sectionId || "shared";
    if (!groups.has(sectionId)) {
      const group = document.createElement("optgroup");
      const external = sectionId !== mapKey && sectionId !== "shared" && scope === "section";
      group.label = (external ? "En uso · " : "") + sectionResourceLabel(sectionId, maps);
      groups.set(sectionId, group);
      children.push(group);
    }
    const option = document.createElement("option");
    option.value = asset[valueField];
    option.textContent = asset.name;
    option.selected = asset[valueField] === previous;
    groups.get(sectionId).append(option);
  }
  if (!children.length) {
    const option = document.createElement("option");
    option.textContent = "Sin recursos en esta sección";
    option.value = "";
    option.disabled = true;
    children.push(option);
  }
  select.replaceChildren(...children);
  if (emptyLabel && !value) select.value = "";
}
