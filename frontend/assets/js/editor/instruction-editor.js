export function createInstructionEditor({ list, addButton, getRoute, onChange }) {
  const read = () => Array.from(list.querySelectorAll("textarea"), (input) => input.value);
  function render(steps) {
    list.replaceChildren(...(steps.length ? steps : [""]).map((text, index) => {
      const row = document.createElement("li");
      const input = document.createElement("textarea");
      input.rows = 2;
      input.value = text;
      input.setAttribute("aria-label", `Paso ${index + 1}`);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "remove-instruction-step";
      remove.dataset.removeStep = index;
      remove.textContent = "\u00d7";
      remove.title = `Eliminar paso ${index + 1}`;
      remove.setAttribute("aria-label", remove.title);
      row.append(input, remove);
      return row;
    }));
  }
  list.addEventListener("input", onChange);
  list.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-step]");
    if (!button || !getRoute()) return;
    const index = Number(button.dataset.removeStep);
    const steps = read();
    steps.splice(index, 1);
    render(steps);
    onChange();
    const inputs = list.querySelectorAll("textarea");
    inputs[Math.min(index, inputs.length - 1)]?.focus();
  });
  addButton.addEventListener("click", () => {
    if (!getRoute()) return;
    render([...read(), ""]);
    onChange();
    list.lastElementChild.querySelector("textarea").focus();
  });
  return { render, read };
}
