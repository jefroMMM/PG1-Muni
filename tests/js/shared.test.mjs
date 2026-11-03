import test from "node:test";
import assert from "node:assert/strict";
import { getInstructionSteps } from "../../frontend/assets/js/shared/instructions.js";
import { getRouteTiming } from "../../frontend/assets/js/shared/route-timing.js";
import { parseHighlight, serializeHighlight, validHighlight } from "../../frontend/assets/js/shared/highlight-area.js";
import { getMapKey, getMapLinks, getSections } from "../../frontend/assets/js/shared/sections.js";
import { clampPoint, findAsset, normalizeSegmentAssets, transformAroundCenter } from "../../frontend/assets/js/shared/map-utils.js";
import { filterResources, sectionResourceLabel } from "../../frontend/assets/js/shared/resource-catalog.js";

test("manual instructions preserve sentences within a step", () => {
  assert.deepEqual(getInstructionSteps({ instructionSteps: ["Gira. Sigue; avanza.", "  Llega  ", ""] }), ["Gira. Sigue; avanza.", "Llega"]);
  assert.deepEqual(getInstructionSteps({ instructionSteps: [], instructions: "Old text" }), []);
  assert.deepEqual(getInstructionSteps({ instructions: "Gira. Sigue." }), ["Gira", "Sigue"]);
});

test("route phases fit inside the total duration", () => {
  for (const seconds of [3, 12.5, 30, 3600]) {
    const timing = getRouteTiming({ durationSeconds: seconds }, { routeRevealTime: 7000, routeExitDuration: 7000 });
    assert.equal(timing.total, seconds * 1000);
    assert.equal(timing.exitAt + timing.exit, timing.resetAt);
    assert.equal(timing.resetAt + timing.panelReturn, timing.total);
    assert.ok(timing.reveal + 360 <= timing.exitAt);
  }
});

test("destination areas reject crossed or degenerate polygons", () => {
  const value = "10,10 100,10 100,100 10,100";
  assert.equal(serializeHighlight(parseHighlight(value)), value);
  assert.ok(validHighlight(parseHighlight(value)));
  for (const value of ["", "10,10 100,100 100,10 10,100", "0,0 10,0 20,0 30,0", "-1,0 10,0 10,10 0,10"]) {
    assert.equal(validHighlight(parseHighlight(value)), false);
  }
});

test("canonical map URLs never use removed builtin aliases", () => {
  assert.equal(getMapKey("/MapaR/Conf"), "mapar");
  assert.equal(getMapKey("/Conf"), "terminal");
  assert.equal(getMapKey("/maps/new-section/Conf"), "new-section");
  assert.deepEqual(getMapLinks("terminal"), { home: "/", editor: "/Conf" });
  assert.deepEqual(getMapLinks("mapar"), { home: "/MapaR/", editor: "/MapaR/Conf" });
  const sections = getSections({ maps: { terminal: {}, mapar: {}, new: { sectionName: "New" } } });
  assert.equal(sections[2].home, "/maps/new");
});

test("segment normalization preserves transformations and matches node count", () => {
  const route = { nodes: [{ x: 1, y: 2 }, { x: 3, y: 4 }, { x: 5, y: 6 }], segmentAssets: ["custom"], segmentOptions: [{ rotation: 45, mirrored: true }] };
  normalizeSegmentAssets(route, "fallback");
  assert.deepEqual(route.segmentAssets, ["custom", "fallback"]);
  assert.deepEqual(route.segmentOptions, [{ rotation: 45, mirrored: true }, { rotation: 0, mirrored: false }]);
  assert.deepEqual(clampPoint({ x: -10, y: 1500 }), { x: 0, y: 1000 });
});

test("asset lookup respects catalog priority and transforms stay centered", () => {
  const route = { id: "same", src: "/route.png" };
  assert.equal(findAsset({ routeAssets: [route], markerIcons: [{ id: "same" }] }, "same"), route);
  assert.equal(findAsset({}, "missing"), undefined);
  assert.equal(transformAroundCenter({ x: 10, y: 20, width: 40, height: 60, rotation: 45, mirrored: true }), "translate(30 50) rotate(45) scale(-1 1) translate(-30 -50)");
});

test("section libraries include shared resources and preserve assigned foreign assets", () => {
  const assets = [
    { id: "own", sectionId: "terminal" }, { id: "other", sectionId: "mapar" },
    { id: "shared", sectionId: "shared" }
  ];
  assert.deepEqual(filterResources(assets, "terminal").map((item) => item.id), ["own", "shared"]);
  assert.equal(filterResources(assets, "terminal", "all").length, 3);
  assert.equal(filterResources(assets, "terminal", "section", ["other"]).length, 3);
  assert.equal(sectionResourceLabel("terminal"), "Mapa");
  assert.equal(sectionResourceLabel("new", { new: { sectionName: "Nueva" } }), "Nueva");
});
