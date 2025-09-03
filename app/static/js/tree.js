/* Gratitude Tree leaf animation + streak glow */
(function () {
  const svg = document.getElementById("gratitudeTree");
  const layer = document.getElementById("leavesLayer");
  if (!svg || !layer) return;

  const leaves = Math.max(0, parseInt(window.__SahAI_LEAVES__ || 0, 10));
  const streak = Math.max(0, parseInt(window.__SahAI_STREAK__ || 0, 10));

  // Branch regions to sprinkle leaves (x,y ranges)
  const regions = [
    { x: [210, 270], y: [120, 200] },
    { x: [330, 390], y: [120, 200] },
    { x: [240, 320], y: [140, 240] },
    { x: [280, 360], y: [150, 240] },
  ];

  function rand(min, max) { return Math.random() * (max - min) + min; }

  for (let i = 0; i < leaves; i++) {
    const r = regions[i % regions.length];
    const cx = rand(r.x[0], r.x[1]);
    const cy = rand(r.y[0], r.y[1]);
    const leaf = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    leaf.setAttribute("cx", cx.toFixed(1));
    leaf.setAttribute("cy", cy.toFixed(1));
    const size = rand(5, 10);
    leaf.setAttribute("r", size.toFixed(1));
    const golden = i < streak && streak >= 2; // first N leaves “golden” for current streak
    leaf.setAttribute("fill", golden ? "#ffd54f" : "#66bb6a");
    leaf.setAttribute("opacity", golden ? "0.95" : "0.9");
    leaf.classList.add("leaf-grow");
    layer.appendChild(leaf);
  }
})();
