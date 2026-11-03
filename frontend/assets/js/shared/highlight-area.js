export function parseHighlight(value = "") {
  return value.trim() ? value.trim().split(/\s+/).map((pair) => {
    const [x, y] = pair.split(",").map(Number);
    return { x, y };
  }) : [];
}

export function serializeHighlight(points) {
  return points.map(({ x, y }) => `${x},${y}`).join(" ");
}

export function validHighlight(points) {
  if (points.length !== 4 || points.some(({ x, y }) => !Number.isFinite(x) || !Number.isFinite(y) || x < 0 || x > 2000 || y < 0 || y > 1000)) return false;
  const turns = points.map((point, index) => {
    const next = points[(index + 1) % 4];
    const end = points[(index + 2) % 4];
    return (next.x - point.x) * (end.y - next.y) - (next.y - point.y) * (end.x - next.x);
  });
  return turns.every((turn) => turn > 0) || turns.every((turn) => turn < 0);
}
