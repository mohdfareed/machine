// Mount a compact action inside the PC card header; mounting sends no request.
(() => {
  if (window.homepageWakePC) return;
  window.homepageWakePC = true;
  const style = document.createElement("style");
  style.textContent = `
    [data-wake-pc] { display:inline-flex; align-items:center; justify-content:center;
      width:32px; height:32px; padding:6px; flex-shrink:0; border:0; border-radius:6px;
      color:var(--color-emerald-500); background:transparent; cursor:pointer; margin:0; box-sizing:border-box; }
    [data-wake-pc]:hover { background:rgba(127,127,127,.15); }
    [data-wake-pc]:focus-visible { outline:2px solid currentColor; outline-offset:2px; }
    [data-wake-pc]:disabled { color:inherit; opacity:.5; cursor:wait; }
  `;
  document.head.append(style);

  function mount() {
    const tile = document.getElementById("pc");
    const card = tile?.querySelector(".service-card");
    const title = card?.querySelector(".service-title");
    const controls = title?.querySelector(".service-tags");
    if (!controls || tile.querySelector("[data-wake-pc]")) return;
    // Use the card padding for equal top/right insets, without changing header height.
    const inset = getComputedStyle(card).paddingTop;
    controls.style.cssText = `position:absolute;top:${inset};right:${inset};align-items:center;gap:6px;margin:0`;
    title.style.paddingRight = "40px";
    const name = title.querySelector(".service-title-text");
    if (name) name.style.minWidth = "0";
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.wakePc = "";
    button.title = "Wake PC";
    button.setAttribute("aria-label", "Wake PC");
    button.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3v9"/><path d="M6.3 5.9a8 8 0 1 0 11.4 0"/></svg>';
    const status = document.createElement("span");
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.style.cssText = "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0";
    button.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (button.disabled) return;
      button.disabled = true;
      button.title = "Wake PC";
      button.setAttribute("aria-label", "Wake PC");
      status.textContent = "Sending…";
      try {
        const response = await fetch(`https://${location.hostname.replace(/^dashboard\./, "homelab.")}/actions/wake-pc`, {
          method: "POST",
          headers: { "X-Wake-PC": "1" },
          mode: "cors",
          credentials: "omit",
          redirect: "error",
          signal: AbortSignal.timeout(10000),
        });
        const result = await response.json();
        status.textContent = response.ok ? "Wake sent" : (result.message || `Wake failed (${response.status})`);
        if (!response.ok) {
          button.title = `Wake PC: ${status.textContent}`;
          button.setAttribute("aria-label", button.title);
        }
      } catch {
        status.textContent = "No confirmation; wake may have been sent.";
        button.title = `Wake PC: ${status.textContent}`;
        button.setAttribute("aria-label", button.title);
      } finally {
        setTimeout(() => { button.disabled = false; }, 5000);
      }
    });
    controls.append(status, button);
  }

  new MutationObserver(mount).observe(document.documentElement, { childList: true, subtree: true });
  mount();
})();
