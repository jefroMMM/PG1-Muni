export function getMapKey(pathname = window.location.pathname) {
  const section = pathname.match(/^\/maps\/([^/]+)/);
  return section ? decodeURIComponent(section[1]) : pathname.toLowerCase().startsWith("/mapar") ? "mapar" : "terminal";
}

export function getMapLinks(key) {
  if (key === "terminal") return { home: "/", editor: "/Conf" };
  if (key === "mapar") return { home: "/MapaR/", editor: "/MapaR/Conf" };
  const home = `/maps/${encodeURIComponent(key)}`;
  return { home, editor: `${home}/Conf` };
}

export function getSections(config) {
  const definitions = {
    terminal: { title: "Mapa", navTitle: "Mapa de oficinas", description: "Recorridos internos · Oficinas de la terminal", icon: "building" },
    mapar: { title: "MapaR", navTitle: "Mapa de Retalhuleu", description: "Recorridos urbanos · Dependencias de Retalhuleu", icon: "map" }
  };
  const maps = config?.maps || { terminal: {}, mapar: {} };
  return ["terminal", "mapar", ...Object.keys(maps).filter((key) => !definitions[key])]
    .filter((key) => Object.hasOwn(maps, key)).map((key) => {
      const map = maps[key];
      const title = map.sectionName || map.title || "Sección";
      return { key, ...getMapLinks(key), ...(definitions[key] || {
        title, navTitle: title, description: "Mapa y recorridos de la sección", icon: map.sectionIcon || "building"
      }) };
    });
}
