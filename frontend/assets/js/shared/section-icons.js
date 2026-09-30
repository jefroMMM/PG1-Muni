export const sectionIcons = {
  building: { name: "Oficinas", shape: '<path d="M4 21V5h16v16M2 21h20M9 21v-6h6v6M8 9h2m4 0h2"/>' },
  map: { name: "Mapa", shape: '<path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2ZM9 3v16M15 5v16"/>' },
  pin: { name: "Ubicación", shape: '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>' },
  briefcase: { name: "Servicios", shape: '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V3h8v4M3 12h18M10 12v3h4v-3"/>' },
  health: { name: "Salud", shape: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M10 7h4v3h3v4h-3v3h-4v-3H7v-4h3Z"/>' },
  school: { name: "Educación", shape: '<path d="m2 8 10-5 10 5-10 5ZM6 10v7c4 3 8 3 12 0v-7M22 8v9"/>' },
  bus: { name: "Transporte", shape: '<rect x="5" y="3" width="14" height="16" rx="3"/><path d="M5 11h14M8 19v2M16 19v2M9 15h.01M15 15h.01M8 6h8"/>' },
  park: { name: "Parque", shape: '<path d="m12 2 5 7h-3l5 7H5l5-7H7ZM12 16v6M8 22h8"/>' }
};

export function sectionIcon(key) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.innerHTML = (sectionIcons[key] || sectionIcons.building).shape;
  return svg;
}
