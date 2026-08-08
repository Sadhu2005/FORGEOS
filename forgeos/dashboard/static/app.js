document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  const btn = form.querySelector("[data-confirm]");
  if (!(btn instanceof HTMLElement)) return;
  const message = btn.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});
