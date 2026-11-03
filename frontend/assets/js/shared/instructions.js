export function getInstructionSteps(route) {
  if (Array.isArray(route.instructionSteps)) {
    return route.instructionSteps.map((step) => step.trim()).filter(Boolean);
  }
  // Preserve the existing presentation when opening routes saved by older editors.
  return (route.instructions || "")
    .replace(/\r/g, "\n")
    .split(/\n+|(?<=\.)\s+|(?<=;)\s+/)
    .map((step) => step.replace(/^\s*\d+[\).\-\s]+/, "").trim())
    .map((step) => step.replace(/\.$/, ""))
    .filter(Boolean);
}
