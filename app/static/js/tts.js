/* Simple SpeechSynthesis helpers with language-aware voice choice. */
let _utter = null;

function _pickVoiceFor(lang) {
  const voices = window.speechSynthesis.getVoices();
  if (!voices || !voices.length) return null;
  // Prefer Indian English / Hindi if available
  const prefs = ["en-IN", "hi-IN", "en-GB", "en-US"];
  for (const p of prefs) {
    const v = voices.find(v => v.lang === p);
    if (v) return v;
  }
  return voices[0];
}

function ttsPlay(text) {
  if (!("speechSynthesis" in window)) return;
  ttsStop();
  _utter = new SpeechSynthesisUtterance(text || "");
  _utter.rate = 1.0;
  _utter.pitch = 1.0;
  _utter.volume = 1.0;
  const v = _pickVoiceFor("en-IN");
  if (v) _utter.voice = v;
  window.speechSynthesis.speak(_utter);
}

function ttsPause() {
  if (!("speechSynthesis" in window)) return;
  if (window.speechSynthesis.speaking) window.speechSynthesis.pause();
}

function ttsStop() {
  if (!("speechSynthesis" in window)) return;
  if (window.speechSynthesis.speaking) window.speechSynthesis.cancel();
  _utter = null;
}

window.speechSynthesis && window.speechSynthesis.onvoiceschanged;
