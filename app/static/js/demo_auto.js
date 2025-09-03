(function () {
  const el = document.getElementById("autoCarousel");
  if (!el) return;
  const carousel = new bootstrap.Carousel(el, { interval: 10000, ride: false });

  const pauseBtn = document.getElementById("pauseBtn");
  const resumeBtn = document.getElementById("resumeBtn");

  pauseBtn?.addEventListener("click", () => {
    carousel.pause();
    window.dispatchEvent(new CustomEvent("toast", { detail: { message: "Auto demo paused" } }));
  });
  resumeBtn?.addEventListener("click", () => {
    carousel.cycle();
    window.dispatchEvent(new CustomEvent("toast", { detail: { message: "Auto demo resumed" } }));
  });
})();
