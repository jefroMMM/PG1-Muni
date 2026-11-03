export function createPreviewController({ getConfig, getRoute, mapKey }) {
  const previewDialog = document.getElementById("previewDialog");
  const previewFrame = document.getElementById("previewFrame");
  let previewSnapshot = null;

  document.getElementById("previewButton").addEventListener("click", () => {
    const route = getRoute();
    if (!route) return;
    previewSnapshot = structuredClone(getConfig());
    // The visitor view receives only this draft. No write request or saved configuration is needed.
    previewSnapshot.maps[mapKey].routes = [{ ...structuredClone(route), archived: false }];
    previewFrame.src = "/preview";
    previewDialog.showModal();
  });
  document.getElementById("closePreviewButton").addEventListener("click", () => previewDialog.close());
  previewDialog.addEventListener("close", () => { previewFrame.src = "about:blank"; previewSnapshot = null; });
  window.addEventListener("message", (event) => {
    if (event.origin !== window.location.origin || event.source !== previewFrame.contentWindow || event.data?.type !== "route-preview-ready" || !previewSnapshot) return;
    previewFrame.contentWindow.postMessage({ type: "route-preview-data", config: previewSnapshot, mapKey, routeId: getRoute()?.id }, window.location.origin);
  });
}
