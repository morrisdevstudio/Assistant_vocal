import { archive, trials } from "./room-calibration.mjs?v=20261125";

const element = id => document.getElementById("room-" + id);
const start = element("start");
const play = element("play");
const accept = element("accept");
const cancel = element("cancel");
const download = element("download");
const restart = element("restart");
const distance = element("distance");
const status = element("status");
const signal = new Audio("/api/room-capture/signal");
signal.preload = "auto";
const tokenKey = "alfred-room-capture";
let token = sessionStorage.getItem(tokenKey);
let takes = [];
let started;
let exportedCount = 0;
let draft = null;
let sweepComplete = false;
let busy = false;
let state = "idle";
let remaining = 12;

function setStatus(message) {
  if (status.textContent !== message) status.textContent = message;
}

async function request(method, path = "") {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["X-Alfred-Capture"] = token;
  const response = await fetch("/api/room-capture" + path, { method, headers, cache: "no-store" });
  if (!response.ok) {
    const error = new Error((await response.json()).detail || "Capture indisponible.");
    error.status = response.status;
    throw error;
  }
  return path === "/wav" ? response.arrayBuffer() : response.json();
}

function clearToken() {
  token = null;
  sessionStorage.removeItem(tokenKey);
}

function render() {
  const trial = trials[takes.length];
  const sweep = trial && !trial.phrase;
  const recording = state === "recording";
  element("progress").textContent = trial
    ? `Étape ${takes.length + 1} sur ${trials.length}`
    : `${takes.length} prises validées`;
  element("title").textContent = trial?.title ?? "Parcours terminé";
  element("instructions").textContent = trial?.instruction ?? "Téléchargez le ZIP pour transmettre les prises.";
  const phrase = element("phrase");
  phrase.hidden = !trial?.phrase;
  phrase.textContent = trial?.phrase ? `« ${trial.phrase} »` : "";
  start.hidden = !trial || Boolean(token) || Boolean(draft);
  start.disabled = busy;
  play.hidden = !sweep || !recording;
  play.disabled = sweepComplete || !signal.paused || remaining < 6;
  accept.hidden = !draft;
  cancel.hidden = !token && !draft;
  cancel.textContent = draft ? "Refaire la prise" : "Annuler la prise";
  download.disabled = takes.length === 0;
  restart.hidden = Boolean(trial);
  restart.disabled = exportedCount !== takes.length;
  distance.disabled = Boolean(token);
}

async function run(action) {
  if (busy) return;
  busy = true;
  try {
    await action();
  } catch (error) {
    setStatus(error.message);
  } finally {
    busy = false;
    render();
  }
}

function stopSignal() {
  signal.pause();
  signal.currentTime = 0;
}

async function update(take) {
  state = take.state;
  remaining = take.remaining;
  if (state === "waiting") {
    setStatus("Attente du flux de l’ESP32…");
  } else if (state === "recording") {
    const trial = trials[takes.length];
    let cue = "Dites la phrase une fois.";
    if (!trial.phrase) {
      if (sweepComplete || !signal.paused) cue = "Gardez le téléphone immobile.";
      else cue = remaining < 6 ? "Trop tard pour jouer le signal. Refaites la prise." : "Jouez le balayage.";
    }
    setStatus(`Enregistrement · ${remaining} s. ${cue}`);
  } else if (state === "ready") {
    const trial = trials[takes.length];
    if (!trial.phrase && !sweepComplete) {
      await request("DELETE");
      stopSignal();
      clearToken();
      state = "idle";
      setStatus("Balayage incomplet. Relancez l’étape et jouez le signal dès que le micro enregistre.");
      return;
    }
    draft = new Uint8Array(await request("GET", "/wav"));
    clearToken();
    setStatus("Prise prête. Validez-la ou refaites-la.");
  } else {
    stopSignal();
    clearToken();
    setStatus(state === "flux_interrompu"
      ? "Flux interrompu. Vérifiez la connexion et relancez l’étape."
      : "Prise indisponible. Relancez l’étape.");
  }
}

start.addEventListener("click", () => run(async () => {
  if (token || draft || !trials[takes.length] || !distance.reportValidity()) return;
  start.disabled = true;
  sweepComplete = false;
  const take = await request("POST");
  started ??= new Date();
  token = take.token;
  sessionStorage.setItem(tokenKey, token);
  await update(take);
}));

play.addEventListener("click", async () => {
  if (play.disabled) return;
  play.disabled = true;
  try {
    signal.currentTime = 0;
    await signal.play();
  } catch {
    setStatus("Lecture impossible. Réessayez ou recommencez la prise.");
    render();
  }
});
signal.addEventListener("ended", () => {
  sweepComplete = true;
  render();
});

accept.addEventListener("click", () => {
  if (!draft) return;
  takes.push({ index: takes.length, data: draft });
  draft = null;
  state = "idle";
  setStatus("");
  render();
});

cancel.addEventListener("click", () => run(async () => {
  if (token) await request("DELETE");
  clearToken();
  stopSignal();
  draft = null;
  state = "idle";
  setStatus("Prise supprimée. Vous pouvez refaire l’étape.");
}));

download.addEventListener("click", () => {
  if (!takes.length || !distance.reportValidity()) return;
  const date = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(started);
  const link = document.createElement("a");
  link.href = URL.createObjectURL(archive(takes, distance.value ? distance.valueAsNumber : null, started));
  link.download = `alfred-salon-${date}${takes.length < trials.length ? "-partiel" : ""}.zip`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 10_000);
  exportedCount = takes.length;
  render();
});

restart.addEventListener("click", () => {
  takes = [];
  started = undefined;
  exportedCount = 0;
  setStatus("");
  render();
});

window.addEventListener("beforeunload", event => {
  if (token || draft || takes.length > exportedCount) {
    event.preventDefault();
    event.returnValue = "";
  }
});

function expired(error) {
  if (error.status !== 404) throw error;
  return { state: "expire" };
}

if (token) {
  // Les WAV déjà validés étaient dans l'ancienne page.
  run(async () => update(await request("DELETE").catch(expired)));
} else {
  render();
}
setInterval(() => {
  if (token) run(async () => update(await request("GET").catch(expired)));
}, 500);
