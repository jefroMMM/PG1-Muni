const routePath = document.getElementById("routePath");
const startPoint = document.getElementById("startPoint");
const endPoint = document.getElementById("endPoint");
const routeLayer = document.getElementById("routeLayer");
const debugToggle = document.getElementById("debugToggle");
const debugOutput = document.getElementById("debugOutput");
const buttons = document.querySelectorAll(".office-button");
const highlights = document.querySelectorAll(".office-highlight");

// Base SVG: 2000 x 1000. La imagen ocupa toda la base para evitar margenes laterales.
// El punto inicial es la Entrada y los tramos siguen pasillos visibles.
const routes = {
  contaduria: "M 1000 877 L 1000 808 L 556 808 L 556 473 L 514 473 L 514 356 L 419 319",
  administracion: "M 1000 877 L 1000 808 L 556 808 L 556 484 L 514 484 L 514 563 L 389 648",
  sala: "M 1000 877 L 1000 808 L 556 808 L 556 473 L 556 313 L 670 287 L 909 260",
  rrhh: "M 1000 877 L 1000 808 L 1423 808 L 1423 473 L 1477 473 L 1477 335 L 1621 282",
  gerencia: "M 1000 877 L 1000 808 L 1423 808 L 1423 473 L 1477 473 L 1477 552 L 1663 648"
};

const routeEnds = {
  contaduria: { x: 419, y: 319 },
  administracion: { x: 389, y: 648 },
  sala: { x: 909, y: 260 },
  rrhh: { x: 1621, y: 282 },
  gerencia: { x: 1663, y: 648 }
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

  // Reinicia la animacion cada vez que se presiona un boton.
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
