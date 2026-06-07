const routePath = document.getElementById("routePath");
const startPoint = document.getElementById("startPoint");
const endPoint = document.getElementById("endPoint");
const routeLayer = document.getElementById("routeLayer");
const debugToggle = document.getElementById("debugToggle");
const debugOutput = document.getElementById("debugOutput");
const buttons = document.querySelectorAll(".office-button");
const highlights = document.querySelectorAll(".office-highlight");

// Coordenadas SVG manuales. El punto inicial es la Entrada y los tramos siguen pasillos visibles.
const routes = {
  contaduria: "M 836 825 L 836 760 L 465 760 L 465 445 L 430 445 L 430 335 L 350 300",
  administracion: "M 836 825 L 836 760 L 465 760 L 465 455 L 430 455 L 430 530 L 325 610",
  sala: "M 836 825 L 836 760 L 465 760 L 465 445 L 465 295 L 560 270 L 760 245",
  rrhh: "M 836 825 L 836 760 L 1190 760 L 1190 445 L 1235 445 L 1235 315 L 1355 265",
  gerencia: "M 836 825 L 836 760 L 1190 760 L 1190 445 L 1235 445 L 1235 520 L 1390 610"
};

const routeEnds = {
  contaduria: { x: 350, y: 300 },
  administracion: { x: 325, y: 610 },
  sala: { x: 760, y: 245 },
  rrhh: { x: 1355, y: 265 },
  gerencia: { x: 1390, y: 610 }
};

function selectRoute(routeName) {
  const route = routes[routeName];
  const end = routeEnds[routeName];

  routePath.setAttribute("d", route);
  endPoint.setAttribute("cx", end.x);
  endPoint.setAttribute("cy", end.y);

  const length = routePath.getTotalLength();
  routePath.style.transition = "none";
  routePath.style.strokeDasharray = length;
  routePath.style.strokeDashoffset = length;

  // Reinicia la animación cada vez que se presiona un botón.
  routePath.getBoundingClientRect();
  routePath.style.transition = "stroke-dashoffset 1.25s ease-in-out";
  routePath.style.strokeDashoffset = "0";

  startPoint.classList.add("visible");
  endPoint.classList.add("visible");

  highlights.forEach((highlight) => highlight.classList.remove("active"));
  document.getElementById(`highlight-${routeName}`).classList.add("active");

  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset.route === routeName);
  });
}

buttons.forEach((button) => {
  button.addEventListener("click", () => selectRoute(button.dataset.route));
});

debugToggle.addEventListener("change", () => {
  debugOutput.hidden = !debugToggle.checked;
  debugOutput.textContent = debugToggle.checked
    ? "Haz clic sobre el mapa para ver coordenadas SVG"
    : "";
});

routeLayer.addEventListener("click", (event) => {
  if (!debugToggle.checked) {
    return;
  }

  const point = routeLayer.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;

  const svgPoint = point.matrixTransform(routeLayer.getScreenCTM().inverse());
  const x = Math.round(svgPoint.x);
  const y = Math.round(svgPoint.y);

  debugOutput.textContent = `x: ${x}, y: ${y}`;
  console.log(`Coordenada SVG: ${x}, ${y}`);
});

selectRoute("contaduria");
