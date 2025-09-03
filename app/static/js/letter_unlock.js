(function(){
  const span = document.getElementById("unlockCountdown");
  if (!span || !window.unlockAt) return;
  function tick() {
    const now = new Date();
    let diff = Math.max(0, (unlockAt - now) / 1000);
    const d = Math.floor(diff / 86400); diff -= d*86400;
    const h = Math.floor(diff / 3600); diff -= h*3600;
    const m = Math.floor(diff / 60);   diff -= m*60;
    const s = Math.floor(diff);
    span.textContent = `${d}d ${h}h ${m}m ${s}s`;
  }
  tick();
  setInterval(tick, 1000);
})();
