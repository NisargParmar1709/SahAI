function copyText(selector) {
  const el = document.querySelector(selector);
  if (!el) return;
  const range = document.createRange();
  range.selectNodeContents(el);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  try {
    document.execCommand("copy");
    sel.removeAllRanges();
    const evt = new CustomEvent("toast", { detail: { message: "Copied to clipboard ✅" } });
    window.dispatchEvent(evt);
  } catch (e) { /* no-op */ }
}
