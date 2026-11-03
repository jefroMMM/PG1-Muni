export function getRouteTiming(route, map) {
  const legacyTotal = (Number(map.routeVisibleTime) || 15000) + (Number(map.routeExitDuration) || 4000) + 1500;
  const seconds = Number(route.durationSeconds);
  const total = Number.isFinite(seconds) && seconds >= 3 && seconds <= 3600 ? seconds * 1000 : legacyTotal;
  const panelReturn = Math.min(1500, total * 0.15);
  const exit = Math.min(Number(map.routeExitDuration) || 4000, total * 0.25);
  const resetAt = total - panelReturn;
  const exitAt = resetAt - exit;
  const reveal = Math.max(0, Math.min(Number(map.routeRevealTime) || 5000, total * 0.3) - 360);
  return { total, panelReturn, exit, resetAt, exitAt, reveal };
}
