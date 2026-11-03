import { loadRouteConfig, createMap } from "./shared/config-api.js";
import { getSections } from "./shared/sections.js";
import { sectionIcons, sectionIcon } from "./shared/section-icons.js";
import { createDashboardActions } from "./dashboard-actions.js";

let maps = getSections();
const groups = document.getElementById("mapGroups");
const status = document.getElementById("dashboardStatus");
const search = document.getElementById("routeSearch");
const filter = document.getElementById("routeFilter");
let config;
let activeView = "inicio";
const dashboardActions = createDashboardActions({ groups, refresh });
const views = {
  inicio: { title: "Administración de rutas", description: "Consulta y configura los recorridos de las oficinas y las dependencias de Retalhuleu.", breadcrumb: "Rutas y mapas", note: "En ambos mapas" },
  terminal: { title: "Mapa de oficinas", description: "Administra únicamente los recorridos internos de las oficinas de la terminal.", breadcrumb: "Mapa de oficinas", note: "En el mapa de oficinas" },
  mapar: { title: "Mapa de Retalhuleu", description: "Administra únicamente los recorridos urbanos de las dependencias de Retalhuleu.", breadcrumb: "Mapa de Retalhuleu", note: "En el mapa de Retalhuleu" }
};

function currentMaps() {
  return activeView === "inicio" ? maps : maps.filter((map) => map.key === activeView);
}

function renderView() {
  const view = views[activeView] || { title: maps.find((map) => map.key === activeView)?.title || "Sección", description: "Administra las rutas y el mapa de esta sección.", breadcrumb: "Secciones", note: "En esta sección" };
  document.querySelector("h1").textContent = view.title;
  document.querySelector(".page-description").textContent = view.description;
  document.querySelector(".topbar strong").textContent = view.breadcrumb;
  document.querySelector(".metric-note").textContent = activeView === "inicio" && maps.length > 2 ? "En todas las secciones" : view.note;
  document.title = `${view.title} | Municipalidad de Retalhuleu`;
  document.querySelectorAll(".nav-link").forEach((link) => {
    const selected = link.getAttribute("href") === `#${activeView}`;
    link.classList.toggle("selected", selected);
    if (selected) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  if (!config) return;
  const routes = currentMaps().flatMap((map) => config.maps[map.key].routes);
  document.getElementById("totalRoutes").textContent = routes.length;
  document.getElementById("visibleRoutes").textContent = routes.filter((route) => !route.archived).length;
  document.getElementById("audioRoutes").textContent = routes.filter((route) => route.audio).length;
  renderGroups();
}

function selectView() {
  const hash = window.location.hash.slice(1);
  const next = hash === "inicio" || maps.some((map) => map.key === hash) ? hash : "inicio";
  if (next !== activeView) { search.value = ""; filter.value = "all"; }
  activeView = next;
  renderView();
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function newTab(label, href, className) {
  const link = element("a", className, label);
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener";
  return link;
}

const normalize = (value) => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

function renderGroups() {
  if (!config) return;
  const query = normalize(search.value.trim());
  let shown = 0;
  const sections = currentMaps().map((map) => {
    const allRoutes = config.maps[map.key].routes;
    const routes = allRoutes.filter((route) => normalize(route.name).includes(query)
      && (filter.value === "all" || (filter.value === "archived" ? route.archived : !route.archived)));
    shown += routes.length;
    const section = element("section", "map-group"); section.id = map.key;
    const heading = element("div", "map-heading");
    const titleBlock = element("div", "map-title-block");
    const title = element("h3");
    title.append(sectionIcon(map.icon || (map.key === "mapar" ? "map" : "building")));
    const returnView = activeView === "inicio" ? "" : `&dashboardView=${activeView}`;
    const mapUrl = `${map.editor}?scope=map&dashboard=2${returnView}`;
    const mapLink = newTab(map.title, mapUrl, "map-title");
    mapLink.title = `Configurar imagen, iconos y decoraciones de ${map.title}`;
    title.append(mapLink, element("span", "map-count", `${allRoutes.length} rutas`));
    const titleLine = element("div", "map-title-line");
    titleLine.append(title, dashboardActions.uploadMenu(map));
    titleBlock.append(titleLine, element("p", "map-description", map.description));
    const actions = element("div", "map-actions");
    actions.append(newTab("Ver mapa ↗", map.home, "view-map"), newTab("Configurar mapa ↗", mapUrl, "configure-map"), newTab("＋ Nueva ruta", `${map.editor}?scope=route&new=1&dashboard=2&dashboardView=${encodeURIComponent(map.key)}`, "primary-action new-route-link"));
    heading.append(titleBlock, actions);
    const table = element("table");
    const caption = element("caption", "sr-only", `Rutas de ${map.title}`);
    const thead = element("thead"); const head = element("tr");
    [["Ruta", "name-cell"], ["Estado", ""], ["Recorrido", "desktop-column"], ["Audio", "desktop-column"], ["Acción", "edit-cell"]].forEach(([label, className]) => {
      const th = element("th", className, label); th.scope = "col"; head.append(th);
    });
    thead.append(head);
    const tbody = element("tbody");
    routes.forEach((route) => {
      const row = element("tr");
      row.dataset.routeId = route.id;
      const name = element("td", "name-cell");
      const href = `${map.editor}?scope=route&route=${encodeURIComponent(route.id)}&dashboard=2${returnView}`;
      const link = newTab("", href, "route-link");
      const dot = element("span", "route-dot"); dot.style.setProperty("--route-color", route.buttonColor || "#177266"); dot.setAttribute("aria-hidden", "true");
      link.append(dot, element("span", "", route.name));
      const nodes = (route.nodes || []).length;
      name.append(link, element("span", "mobile-meta", `${nodes} nodos · ${route.audio ? "Con audio" : "Sin audio"}`));
      const state = element("td"); state.append(element("span", `status-pill${route.archived ? " archived" : ""}`, route.archived ? "Archivada" : "Visible"));
      const action = element("td", "edit-cell");
      const rowActions = element("div", "row-actions");
      const edit = newTab("Editar ↗", href, "edit-link"); edit.setAttribute("aria-label", `Editar ${route.name}`);
      rowActions.append(edit, ...dashboardActions.routeButtons(map, route));
      action.append(rowActions);
      row.append(name, state, element("td", "desktop-column numeric", `${nodes} nodos`), element("td", "desktop-column", route.audio ? "Con audio" : "Sin audio"), action);
      tbody.append(row);
    });
    if (!routes.length) {
      const row = element("tr"); const cell = element("td", "empty-row", allRoutes.length ? "No hay rutas que coincidan con los filtros." : "No hay rutas registradas en este mapa.");
      cell.colSpan = 5; row.append(cell); tbody.append(row);
    }
    table.append(caption, thead, tbody); section.append(heading, table);
    return section;
  });
  groups.replaceChildren(...sections);
  document.getElementById("resultCount").textContent = `${shown} ${shown === 1 ? "ruta encontrada" : "rutas encontradas"}`;
}

async function refresh() {
  try {
    config = await loadRouteConfig();
    maps = getSections(config);
    const nav = document.querySelector(".sidebar nav");
    const summary = nav.querySelector('[href="#inicio"]');
    nav.replaceChildren(summary, ...maps.map((map) => {
      const link = element("a", "nav-link"); link.href = `#${map.key}`;
      link.append(sectionIcon(map.icon), element("span", "", map.navTitle));
      return link;
    }));
    selectView(); status.textContent = "";
  } catch (error) { status.textContent = error.message; }
}

search.addEventListener("input", renderGroups);
filter.addEventListener("change", renderGroups);
document.querySelector(".sidebar nav").addEventListener("click", (event) => {
  const link = event.target.closest(".nav-link");
  if (!link) return;
  event.preventDefault();
  const hash = link.getAttribute("href");
  if (window.location.hash === hash) selectView();
  else window.location.hash = hash;
  window.scrollTo({ top: 0, behavior: "instant" });
});
window.addEventListener("hashchange", selectView);
window.addEventListener("focus", refresh);
selectView();
refresh();

const sectionDialog = document.getElementById("sectionDialog");
const formStatus = document.getElementById("sectionFormStatus");
const catalog = document.getElementById("sectionIconCatalog");
Object.entries(sectionIcons).forEach(([key, icon], index) => {
  const label = element("label", "icon-choice");
  const radio = element("input"); radio.type = "radio"; radio.name = "sectionIcon"; radio.value = key; radio.defaultChecked = index === 0; radio.checked = index === 0;
  label.append(radio, sectionIcon(key), element("span", "", icon.name)); catalog.append(label);
});
document.getElementById("newSectionButton").addEventListener("click", () => {
  document.getElementById("sectionForm").reset(); formStatus.textContent = ""; sectionDialog.showModal();
});
document.getElementById("closeSectionDialog").addEventListener("click", () => sectionDialog.close());
document.getElementById("cancelSectionButton").addEventListener("click", () => sectionDialog.close());
document.getElementById("sectionForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = document.getElementById("sectionName").value.trim();
  if (!name) { formStatus.textContent = "Escribe el nombre de la sección."; return; }
  const button = document.getElementById("createSectionButton"); button.disabled = true; formStatus.textContent = "Creando sección…";
  try {
    const result = await createMap({ name, icon: document.querySelector('[name="sectionIcon"]:checked').value, template: document.getElementById("sectionTemplate").value });
    await refresh(); sectionDialog.close(); window.location.hash = result.mapKey;
  } catch (error) { formStatus.textContent = error.message; }
  finally { button.disabled = false; }
});
