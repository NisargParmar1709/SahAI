/* Simple Web Speech API dictation helper for the journal page. */
(function () {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micBtn = document.getElementById("micBtn");
  const statusEl = document.getElementById("micStatus");
  const textarea = document.getElementById("text");

  if (!micBtn || !statusEl || !textarea) return;

  if (!SpeechRecognition) {
    micBtn.style.display = "none";
    statusEl.innerText = "Voice dictation not supported on this browser.";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.interimResults = true;
  recognition.continuous = true;

  let isOn = false;
  micBtn.addEventListener("click", function () {
    if (!isOn) {
      recognition.start();
      isOn = true;
      micBtn.classList.remove("btn-outline-secondary");
      micBtn.classList.add("btn-danger");
      statusEl.innerText = "Listening…";
      micBtn.querySelector("i").classList.remove("bi-mic");
      micBtn.querySelector("i").classList.add("bi-mic-fill");
    } else {
      recognition.stop();
    }
  });

  recognition.onresult = function (event) {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        textarea.value = (textarea.value + " " + transcript).trim();
      } else {
        interim += transcript;
      }
    }
    statusEl.innerText = interim ? "Listening… " + interim : "Listening…";
  };

  recognition.onerror = function () {
    statusEl.innerText = "Mic error; try again.";
  };

  recognition.onend = function () {
    isOn = false;
    micBtn.classList.remove("btn-danger");
    micBtn.classList.add("btn-outline-secondary");
    micBtn.querySelector("i").classList.remove("bi-mic-fill");
    micBtn.querySelector("i").classList.add("bi-mic");
    statusEl.innerText = "Mic idle";
  };
})();
