// ============================================================================
// MARK: Load the wake control
// ============================================================================
(() => {
  if (window.homepageWakePC) return;
  window.homepageWakePC = true;

  const stylesheet = document.createElement("link");
  stylesheet.rel = "stylesheet";
  stylesheet.href = "/wake-pc.css";
  document.head.append(stylesheet);

  // ==========================================================================
  // MARK: Mount the PC header action
  // ==========================================================================
  function mount() {
    const tile = document.getElementById("pc");
    const title = tile?.querySelector(".service-card .service-title");
    const controls = title?.querySelector(".service-tags");
    if (!controls || tile.querySelector("[data-wake-pc]")) return;

    // Reuse the Docker health indicator's button, padding, and hover classes.
    const button = document.createElement("button");
    button.type = "button";
    button.className = "shrink-0 flex items-center justify-center cursor-pointer service-tag";
    button.dataset.wakePc = "";
    button.title = "Wake PC";
    button.setAttribute("aria-label", "Wake PC");

    const indicator = document.createElement("span");
    indicator.className =
      "w-auto text-center overflow-hidden p-4 rounded-b-[3px] " + "hover:bg-theme-500/10 dark:hover:bg-theme-900/20";
    const icon = document.createElement("span");
    icon.className = "block h-3 w-3 bg-emerald-500 wake-pc-icon";
    icon.setAttribute("aria-hidden", "true");
    indicator.append(icon);
    button.append(indicator);

    const status = document.createElement("span");
    status.className = "sr-only";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");

    // Send only on activation; the server owns the cooldown.
    button.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (button.disabled) return;

      button.disabled = true;
      button.title = "Wake PC";
      button.setAttribute("aria-label", "Wake PC");
      status.textContent = "Sending…";

      try {
        const hostname = location.hostname.replace(/^dashboard\./, "homelab.");
        const response = await fetch(`https://${hostname}/actions/wake-pc`, {
          method: "POST",
          headers: { "X-Wake-PC": "1" },
          mode: "cors",
          credentials: "omit",
          redirect: "error",
          signal: AbortSignal.timeout(10000),
        });
        const result = await response.json();
        const fallback = response.ok ? "Wake request sent" : `Wake failed (${response.status})`;
        status.textContent = result.message || fallback;
      } catch {
        status.textContent = "No confirmation; wake may have been sent.";
      } finally {
        button.disabled = false;
      }

      // Make the response available on hover and on the next focus, too.
      button.title = `Wake PC: ${status.textContent}`;
      button.setAttribute("aria-label", button.title);
    });
    controls.append(status, button);
  }

  // ==========================================================================
  // MARK: Restore the control after rerenders
  // ==========================================================================
  new MutationObserver(mount).observe(document.documentElement, { childList: true, subtree: true });
  mount();
})();
