(function () {
  const frame = document.getElementById("shotFrame");
  const goBtn = document.getElementById("goBtn");
  const sel = document.getElementById("pageSelect");
  const shotBtn = document.getElementById("shotBtn");

  goBtn?.addEventListener("click", () => {
    const path = sel.value || "/journal";
    frame.src = path;
  });

  shotBtn?.addEventListener("click", async () => {
    try {
      const doc = frame.contentDocument;
      if (!doc) throw new Error("Preview not ready");
      // Capture iframe body (same-origin)
      const canvas = await html2canvas(doc.body, { useCORS: true, logging: false, backgroundColor: "#ffffff", scale: 2 });
      const data = canvas.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = data;
      a.download = "sahai_screenshot.png";
      a.click();
      window.dispatchEvent(new CustomEvent("toast", { detail: { message: "Screenshot saved" } }));
    } catch (e) {
      console.error(e);
      window.dispatchEvent(new CustomEvent("toast", { detail: { message: "Unable to capture (try reloading)" } }));
    }
  });
})();
