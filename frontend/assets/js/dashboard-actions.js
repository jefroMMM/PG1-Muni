import { deleteRoute, setRouteArchived, uploadFile } from "./shared/config-api.js";

export function actionIcon(name) {
  const image = document.createElement("img");
  image.src = `/assets/icons/ui/${name}.svg`;
  image.alt = "";
  image.width = image.height = 18;
  return image;
}

export function createDashboardActions({ groups, refresh }) {
  const notice = document.getElementById("dashboardNotice");
  const fileInput = document.getElementById("dashboardUploadInput");
  const dialog = document.getElementById("deleteRouteDialog");
  const confirm = document.getElementById("confirmDeleteRoute");
  const cancel = document.getElementById("cancelDeleteRoute");
  const pending = new Set();
  let deletion = null;
  let uploadTarget = null;
  let uploading = false;

  function announce(message, error = false) {
    notice.textContent = message;
    notice.classList.toggle("error", error);
  }

  async function mutate(map, route, action) {
    const key = `${map.key}:${route.id}`;
    if (pending.has(key)) return false;
    pending.add(key);
    for (const button of groups.querySelectorAll("button[data-route-id]")) {
      if (button.dataset.mapKey === map.key && button.dataset.routeId === route.id) button.disabled = true;
    }
    try {
      if (action === "delete") await deleteRoute(map.key, route.id);
      else await setRouteArchived(map.key, route.id, !route.archived);
      await refresh();
      announce(action === "delete" ? `Ruta «${route.name}» borrada.` : `Ruta «${route.name}» ${route.archived ? "restaurada" : "archivada"}.`);
      return true;
    } catch (error) {
      announce(error.message, true);
      return false;
    } finally {
      pending.delete(key);
      for (const button of groups.querySelectorAll("button[data-route-id]")) {
        if (button.dataset.mapKey === map.key && button.dataset.routeId === route.id) button.disabled = false;
      }
    }
  }

  function routeButtons(map, route) {
    return ["archive", "delete"].map((action) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `route-action-button${action === "delete" ? " delete-action" : ""}`;
      button.dataset.routeAction = action;
      button.dataset.mapKey = map.key;
      button.dataset.routeId = route.id;
      const label = action === "delete" ? "Borrar" : route.archived ? "Restaurar" : "Archivar";
      button.title = `${label} ${route.name}`;
      button.setAttribute("aria-label", button.title);
      button.disabled = pending.has(`${map.key}:${route.id}`);
      button.append(actionIcon(action === "delete" ? "trash-2" : route.archived ? "archive-restore" : "archive"));
      button.addEventListener("click", () => {
        if (action !== "delete") { void mutate(map, route, action); return; }
        deletion = { map, route };
        document.getElementById("deleteRouteTitle").textContent = `Borrar «${route.name}»`;
        document.getElementById("deleteRouteStatus").textContent = "";
        dialog.showModal();
        cancel.focus();
      });
      return button;
    });
  }

  document.getElementById("deleteRouteForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!deletion || confirm.disabled) return;
    confirm.disabled = cancel.disabled = true;
    const { map, route } = deletion;
    document.getElementById("deleteRouteStatus").textContent = "Borrando ruta…";
    try {
      if (await mutate(map, route, "delete")) dialog.close();
      else document.getElementById("deleteRouteStatus").textContent = notice.textContent;
    } finally {
      confirm.disabled = cancel.disabled = false;
    }
  });
  cancel.addEventListener("click", () => dialog.close());
  dialog.addEventListener("cancel", (event) => { if (confirm.disabled) event.preventDefault(); });
  dialog.addEventListener("close", () => { deletion = null; });

  function uploadMenu(map) {
    const menu = document.createElement("details");
    menu.className = "resource-upload-menu";
    const summary = document.createElement("summary");
    summary.append(actionIcon("upload"), document.createTextNode("Subir archivos"));
    summary.setAttribute("aria-label", `Subir archivos a ${map.title}`);
    const options = document.createElement("div");
    options.className = "resource-upload-options";
    for (const [kind, label, icon] of [
      ["audio", "Subir audio", "audio-lines"], ["route-asset", "Subir asset", "footprints"],
      ["map", "Subir fondo", "image"], ["icon", "Subir icono", "map-pin"],
      ["decoration", "Subir decoración", "flower-2"]
    ]) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.uploadKind = kind;
      button.dataset.mapKey = map.key;
      button.append(actionIcon(icon), document.createTextNode(label));
      button.disabled = uploading;
      button.addEventListener("click", () => {
        uploadTarget = { map, kind };
        fileInput.accept = kind === "audio" ? "audio/*" : "image/*";
        fileInput.value = "";
        menu.open = false;
        fileInput.click();
      });
      options.append(button);
    }
    summary.addEventListener("click", () => {
      for (const other of groups.querySelectorAll("details[open]")) if (other !== menu) other.open = false;
    });
    menu.append(summary, options);
    return menu;
  }

  fileInput.addEventListener("cancel", () => { uploadTarget = null; });
  fileInput.addEventListener("change", async () => {
    const files = [...fileInput.files];
    if (!uploadTarget || !files.length || uploading) return;
    const { map, kind } = uploadTarget;
    uploadTarget = null;
    uploading = true;
    let completed = 0;
    try {
      for (const button of groups.querySelectorAll("[data-upload-kind]")) button.disabled = true;
      for (const file of files) {
        announce(`Subiendo ${completed + 1} de ${files.length} a ${map.title}…`);
        await uploadFile(file, kind, map.key);
        completed += 1;
      }
      await refresh();
      announce(kind === "map" ? `${completed} fondo(s) añadido(s) a la biblioteca compartida.` : `${completed} archivo(s) añadido(s) a ${map.title}.`);
    } catch (error) {
      announce(`${completed} de ${files.length} archivos subidos. ${error.message}`, true);
      await refresh();
    } finally {
      uploading = false;
      fileInput.value = "";
      for (const button of groups.querySelectorAll("[data-upload-kind]")) button.disabled = false;
    }
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".resource-upload-menu")) {
      for (const menu of groups.querySelectorAll("details[open]")) menu.open = false;
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") for (const menu of groups.querySelectorAll("details[open]")) menu.open = false;
  });
  return { routeButtons, uploadMenu };
}
