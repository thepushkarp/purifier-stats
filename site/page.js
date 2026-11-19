const explanations = {
  pm2_5_ug_m3: "12 µg/m³ of fine airborne particles.",
  temperature_c: "22.5 °C at the purifier’s temperature sensor.",
  humidity_percent: "45% relative humidity at the purifier.",
  filter_life_percent: "84% of the estimated filter life remains.",
  power: "The purifier is switched on.",
  mode: "Auto mode adjusts the fan speed in response to air quality.",
};
const fields = document.querySelectorAll("[data-field]");
const lines = document.querySelectorAll("[data-line]");
for (const button of fields) {
  button.addEventListener("click", () => {
    for (const field of fields)
      field.setAttribute("aria-pressed", String(field === button));
    for (const line of lines)
      line.classList.toggle(
        "chosen",
        line.dataset.line === button.dataset.field,
      );
    document.querySelector(".explanation").textContent =
      explanations[button.dataset.field];
  });
}
for (const button of document.querySelectorAll(".copy")) {
  button.addEventListener("click", async () => {
    const code = button.parentElement.querySelector("code");
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = "Copied";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(code);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = "Selected";
    }
    setTimeout(() => {
      button.textContent = "Copy";
    }, 1800);
  });
}
