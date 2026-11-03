import { uploadFile } from "../shared/config-api.js";

export function bindCatalogUploads({ elements, mapKey, getCatalog, getMap, getRoute, onChange, renderers }) {
  const uploads = [
    { input: "routeAssetUploadInput", kind: "route-asset", group: "routeAssets", render: "segments" },
    { input: "backgroundUploadInput", kind: "map", group: "backgrounds", render: "background" },
    { input: "iconUploadInput", kind: "icon", group: "markerIcons", render: "markers" },
    { input: "decorationUploadInput", kind: "decoration", group: "decorations", render: "decorations" },
    { input: "audioUploadInput", kind: "audio", group: "audios", render: "audio" }
  ];
  for (const definition of uploads) {
    const input = elements[definition.input];
    input.addEventListener("change", async () => {
      const file = input.files?.[0];
      const route = getRoute();
      if (!file || (definition.kind === "audio" && !route)) return;
      input.disabled = true;
      elements.saveStatus.textContent = "Subiendo archivo...";
      try {
        const uploaded = await uploadFile(file, definition.kind, mapKey);
        const catalog = getCatalog();
        (catalog[definition.group] ||= []).push(uploaded);
        if (definition.kind === "map") {
          getMap().background = uploaded.src;
          elements.mapImage.src = uploaded.src;
        }
        if (definition.kind === "audio") route.audio = uploaded.src;
        input.value = "";
        onChange();
        renderers[definition.render](route);
        if (definition.kind === "icon") elements.markerAssetSelect.value = uploaded.id;
        if (definition.kind === "decoration") elements.decorationAssetSelect.value = uploaded.id;
      } catch (error) {
        elements.saveStatus.textContent = error.message;
        elements.saveStatus.classList.add("dirty");
      } finally {
        input.disabled = false;
      }
    });
  }
}
