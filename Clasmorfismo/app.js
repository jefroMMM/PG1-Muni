(() => {
  const $ = (id) => document.getElementById(id);
  const controls = $("routeControls");
  const panel = $("guidePanel");
  const path = $("routePath");
  const dots = $("routeDots");
  let audio;
  const audioFiles = { contaduria: "AudioContaduria.mp3", administracion: "Audio Administración.mp3", sala: "Sala de reuniones.mp3", rrhh: "Recursos humanos.mp3", gerencia: "Audio gerencia.mp3" };

  const escapeHtml = (value) => String(value || "").replace(/[&<>"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char]);
  const steps = (text) => String(text || "Ruta sin indicaciones disponibles.").split(/(?<=\.)\s+|\n+/).map((step) => step.trim()).filter(Boolean);
  const routeD = (nodes) => nodes.map((node, index) => `${index ? "L" : "M"}${node.x},${node.y}`).join(" ");

  function renderDots(nodes, color) {
    dots.replaceChildren();
    nodes.slice(1).forEach((end, index) => {
      const start = nodes[index]; const length = Math.hypot(end.x - start.x, end.y - start.y); const count = Math.max(2, Math.floor(length / 55));
      for (let step = 1; step < count; step += 1) {
        const ratio = step / count; const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", start.x + (end.x - start.x) * ratio); circle.setAttribute("cy", start.y + (end.y - start.y) * ratio); circle.setAttribute("r", "7"); circle.style.fill = color; dots.append(circle);
      }
    });
  }

  function showWelcome(map) {
    path.setAttribute("d", ""); dots.replaceChildren();
    const welcome = map.defaultPanel || {};
    panel.innerHTML = `<span class="eyebrow">Municipalidad de Retalhuleu</span><h2>${escapeHtml(welcome.title || "Bienvenido")}</h2><p>${escapeHtml(welcome.text || "Selecciona una oficina para ver el recorrido.")}</p><div class="guide-note">${escapeHtml(welcome.hint || "Elige una oficina en los botones inferiores.")}</div>`;
  }

  function showRoute(route) {
    const color = route.buttonColor || "#193879"; path.setAttribute("d", routeD(route.nodes)); path.style.stroke = color; renderDots(route.nodes, color);
    panel.innerHTML = `<span class="eyebrow">Ruta seleccionada</span><h2>${escapeHtml(route.name)}</h2><ol>${steps(route.instructions).map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol><div class="guide-note">La ruta se muestra sobre el croquis.</div>`;
    controls.querySelectorAll("button").forEach((button) => button.classList.toggle("is-active", button.dataset.id === route.id));
    if (audio) { audio.pause(); audio = null; }
    const file = audioFiles[route.id]; if (file) { audio = new Audio(`assets/audios/${encodeURIComponent(file)}`); audio.play().catch(() => {}); }
  }

  fetch("/api/config", { cache: "no-store" }).then((response) => response.ok ? response.json() : Promise.reject()).then((config) => {
    const map = config.maps?.terminal; if (!map) throw new Error();
    document.title = map.title; showWelcome(map);
    (map.routes || []).filter((route) => !route.archived).forEach((route) => {
      const button = document.createElement("button"); button.type = "button"; button.dataset.id = route.id; button.style.setProperty("--route-color", route.buttonColor || "#193879"); button.textContent = route.name; button.addEventListener("click", () => showRoute(route)); controls.append(button);
    });
  }).catch(() => { panel.innerHTML = "<h2>No se pudo cargar la guía</h2><p>Verifica que el servidor esté en funcionamiento.</p>"; });
})();
