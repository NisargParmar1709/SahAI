/* HTML5 canvas doodle tool with undo/clear and PNG export to hidden field. */
(function () {
  const canvas = document.getElementById("doodleCanvas");
  const imgInput = document.getElementById("image_data");
  if (!canvas || !imgInput) return;

  const ctx = canvas.getContext("2d");
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const sizeEl = document.getElementById("brushSize");
  const colorEl = document.getElementById("brushColor");
  const undoBtn = document.getElementById("undoBtn");
  const clearBtn = document.getElementById("clearBtn");

  let drawing = false, lastX = 0, lastY = 0;
  let stack = [];

  function saveState() {
    try { stack.push(canvas.toDataURL("image/png")); if (stack.length > 20) stack.shift(); } catch (e) {}
  }
  function start(e) {
    drawing = true;
    const rect = canvas.getBoundingClientRect();
    lastX = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    lastY = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    saveState();
  }
  function move(e) {
    if (!drawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    ctx.strokeStyle = colorEl.value;
    ctx.lineWidth = parseInt(sizeEl.value, 10) || 5;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();
    lastX = x; lastY = y;
  }
  function end() {
    drawing = false;
    // Update hidden field
    imgInput.value = canvas.toDataURL("image/png");
  }

  canvas.addEventListener("mousedown", start);
  canvas.addEventListener("mousemove", move);
  window.addEventListener("mouseup", end);
  canvas.addEventListener("touchstart", start, { passive: true });
  canvas.addEventListener("touchmove", move, { passive: true });
  canvas.addEventListener("touchend", end);

  undoBtn && undoBtn.addEventListener("click", function () {
    if (!stack.length) return;
    const data = stack.pop();
    const img = new Image();
    img.onload = function () { ctx.drawImage(img, 0, 0); imgInput.value = canvas.toDataURL("image/png"); };
    img.src = data;
  });

  clearBtn && clearBtn.addEventListener("click", function () {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    imgInput.value = canvas.toDataURL("image/png");
  });
})();
