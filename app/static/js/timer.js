/* Minimal countdown timer for meditation page. */
let _timer = null, _remain = 0;

function _renderTimer() {
  const el = document.getElementById("timerDisplay");
  if (!el) return;
  const m = Math.floor(_remain / 60).toString().padStart(2, "0");
  const s = Math.floor(_remain % 60).toString().padStart(2, "0");
  el.textContent = `${m}:${s}`;
}

function timerStart(sec) {
  if (!_remain) _remain = sec || 180;
  if (_timer) clearInterval(_timer);
  _timer = setInterval(() => {
    if (_remain <= 0) {
      clearInterval(_timer);
      _timer = null;
      return;
    }
    _remain -= 1;
    _renderTimer();
  }, 1000);
  _renderTimer();
}

function timerPause() {
  if (_timer) { clearInterval(_timer); _timer = null; }
}

function timerReset() {
  timerPause();
  _remain = 0;
  _renderTimer();
}
