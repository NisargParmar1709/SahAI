// Placeholder for future interactions (animations, toasts, etc.)
(function () {
  // Carousel gentle auto-ride
  const el = document.querySelector('#heroCarousel');
  if (el && window.bootstrap) {
    const carousel = new bootstrap.Carousel(el, {
      interval: 3500,
      pause: false,
      ride: true
    });
  }

  // Subtle page fade-in (progressive enhancement)
  document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('loaded');
  });
})();
