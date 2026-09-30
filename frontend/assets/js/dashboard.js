import { loadRouteConfig } from "./shared/config-api.js";

const groups = document.getElementById("mapGroups");
const status = document.getElementById("dashboardStatus");
const maps = [
  { key: "terminal", title: "Mapa", editor: "/Conf", home: "/" },
  { key: "mapar", title: "MapaR", editor: "/MapaR/Conf", home: "/MapaR/" }
];

function editorLink(label, url) {
  const link = document.createElement("a");
  link.href = url;
  link.textContent = label;
  link.target = "_blank";
  link.rel = "noopener";
  return link;
}

async function renderDashboard() {
  try {
    const config = await loadRouteConfig();
    const sections = maps.map((map) => {
      const section = document.createElement("section");
      section.className = "map-group";
      const heading = document.createElement("div");
      heading.className = "group-heading";
      const titleBlock = document.createElement("div");
      const title = document.createElement("h2");
      const mapLink = editorLink(map.title, `${map.editor}?scope=map`);
      mapLink.className = "map-title";
      mapLink.title = `Configurar imagen, iconos y decoraciones de ${map.title}`;
      title.append(mapLink);
      const hint = document.createElement("p");
      hint.className = "group-hint";
      hint.textContent = "Pulsa el título para configurar el mapa";
      titleBlock.append(title, hint);
      const view = document.createElement("a");
      view.href = map.home; view.target = "_blank"; view.rel = "noopener";
      view.className = "view-map"; view.textContent = "Ver mapa ↗";
      heading.append(titleBlock, view);
      const grid = document.createElement("div");
      grid.className = "route-grid";
      for (const route of config.maps[map.key].routes) {
        const card = editorLink("", `${map.editor}?scope=route&route=${encodeURIComponent(route.id)}`);
        card.className = `route-card${route.archived ? " archived" : ""}`;
        card.style.setProperty("--route-color", route.buttonColor || "#147a69");
        const name = document.createElement("span"); name.className = "route-name"; name.textContent = route.name;
        const meta = document.createElement("span"); meta.className = "route-meta";
        meta.textContent = `${route.archived ? "Archivada" : "Visible"} · ${(route.nodes || []).length} nodos · ${route.audio ? "Con audio" : "Sin audio"}`;
        const action = document.createElement("span"); action.className = "route-action"; action.textContent = "Editar ruta ↗";
        card.append(name, meta, action); grid.append(card);
      }
      if (!grid.childElementCount) grid.textContent = "No hay rutas configuradas en este mapa.";
      section.append(heading, grid);
      return section;
    });
    groups.replaceChildren(...sections);
    status.textContent = "";
  } catch (error) { status.textContent = error.message; }
}

window.addEventListener("focus", renderDashboard);
renderDashboard();
