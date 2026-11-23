import { encodeWav } from "./audio-utils.mjs";

const PHRASES = [
  "Alfred, éteins la lumière du salon s'il te plaît.",
  "Mets un minuteur de huit minutes pour la cuisson.",
  "Quelle heure est-il ? J'aimerais savoir ce qu'il me reste à faire aujourd'hui.",
];
const PASSAGES = 2;
const MAX_SECONDS = 6;

const state = { profiles: [], model: "", enrollment: null, recorder: null, countdown: null, identity: null };
const el = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = "Erreur " + response.status + ".";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch (_) {}
    throw new Error(message);
  }
  return response.json();
}

function button(label, handler, className = "") {
  const element = document.createElement("button");
  element.type = "button";
  element.textContent = label;
  if (className) element.className = className;
  element.addEventListener("click", handler);
  return element;
}

class Recorder {
  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      video: false,
    });
    this.context = new AudioContext();
    await this.context.audioWorklet.addModule("/static/recorder-worklet.js");
    this.node = new AudioWorkletNode(this.context, "alfred-recorder");
    this.chunks = [];
    this.node.port.onmessage = (event) => {
      if (event.data instanceof Float32Array) this.chunks.push(event.data);
    };
    this.source = this.context.createMediaStreamSource(this.stream);
    this.source.connect(this.node);
    this.node.connect(this.context.destination);
    await this.context.resume();
  }

  async stop() {
    const wav = encodeWav(this.chunks, this.context.sampleRate);
    this.close();
    return new Blob([wav], { type: "audio/wav" });
  }

  close() {
    try { this.node?.disconnect(); } catch (_) {}
    try { this.source?.disconnect(); } catch (_) {}
    this.stream?.getTracks().forEach((track) => track.stop());
    if (this.context && this.context.state !== "closed") this.context.close().catch(() => {});
  }
}

function status(text, tone = "") {
  const element = el("profiles-feedback");
  if (!element) return;
  element.textContent = text;
  element.dataset.tone = tone;
}

function render() {
  const list = el("profiles-list");
  if (!list) return;
  const badge = el("profiles-state");
  if (badge) {
    badge.textContent = state.profiles.length
      ? state.profiles.length + (state.profiles.length > 1 ? " profils" : " profil")
      : "Aucun profil";
  }
  if (!state.profiles.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Aucun profil enregistré pour l'instant.";
    list.replaceChildren(empty);
    return;
  }
  list.replaceChildren(...state.profiles.map(row));
}

function row(profile) {
  const article = document.createElement("article");
  article.className = "profile-row";

  const head = document.createElement("div");
  head.className = "profile-head";
  const name = document.createElement("h3");
  name.textContent = profile.name;
  const role = document.createElement("span");
  role.className = "badge";
  role.textContent = profile.role === "child" ? "Enfant" : "Adulte";
  head.append(name, role);

  const count = document.createElement("p");
  count.className = "hint";
  const total = PHRASES.length * PASSAGES;
  count.textContent = profile.samples + " échantillon" + (profile.samples > 1 ? "s" : "")
    + " sur " + total + (profile.samples >= total ? " · enrôlement complet" : "");

  const actions = document.createElement("div");
  actions.className = "voice-actions";
  const complete = profile.samples >= total;
  const label = complete ? "Réenrôler la voix" : (profile.samples ? "Compléter l'enrôlement" : "Enrôler la voix");
  const enroll = button(label, () => startEnrollment(profile));
  enroll.disabled = !state.speakerReady;
  const listen = button("Réécouter", () => playLast(profile), "secondary");
  listen.disabled = !profile.samples;
  const test = button("Tester ma voix", () => testIdentity(profile), "secondary");
  test.disabled = !complete || !state.speakerReady || !!state.recorder;
  const remove = button("Supprimer", () => removeProfile(profile), "secondary");
  actions.append(enroll, listen, test, remove);

  article.append(head, count, actions);
  return article;
}

function renderEnrollment() {
  const panel = el("enrollment");
  if (!panel) return;
  const session = state.enrollment;
  if (!session) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  const total = PHRASES.length * PASSAGES;
  const step = session.step;
  el("enrollment-name").textContent = "Enrôlement de " + session.profile.name;
  const progress = el("enrollment-progress");
  progress.textContent = step + " / " + total + " enregistré" + (step > 1 ? "s" : "");
  if (step >= total) {
    el("enrollment-phrase").textContent = "Enrôlement complet.";
    el("enrollment-text").textContent = "Les six passages sont enregistrés. Utilisez « Réenrôler la voix » pour recommencer.";
    el("enroll-record").disabled = true;
    return;
  }
  const phrase = Math.floor(step / PASSAGES);
  const passage = step % PASSAGES;
  el("enrollment-phrase").textContent = "Phrase " + (phrase + 1) + " sur " + PHRASES.length
    + " · passage " + (passage + 1) + " sur " + PASSAGES;
  el("enrollment-text").textContent = "« " + PHRASES[phrase] + " »";
  el("enroll-record").disabled = state.recorder !== null;
}

async function startEnrollment(profile) {
  const total = PHRASES.length * PASSAGES;
  let step = Math.min(profile.samples, total);
  try {
    if (step >= total) {
      const confirmed = window.confirm("Réenrôler « " + profile.name + " » effacera ses "
        + total + " échantillons audio actuels. Continuer ?");
      if (!confirmed) return;
      await api("/api/profiles/" + profile.id + "/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      profile.samples = 0;
      step = 0;
      await refresh();
    }
  } catch (error) {
    status(error.message, "error");
    return;
  }
  state.enrollment = { profile, step };
  status("Dites la phrase affichée, d'une voix naturelle, à environ un mètre du micro.", "");
  renderEnrollment();
}

async function toggleRecording() {
  const session = state.enrollment;
  if (!session) return;
  const record = el("enroll-record");

  if (state.recorder) {
    record.disabled = true;
    try {
      const blob = await state.recorder.stop();
      state.recorder = null;
      await upload(blob);
    } catch (error) {
      status(error.message, "error");
    } finally {
      record.disabled = false;
      renderEnrollment();
    }
    return;
  }

  try {
    const recorder = new Recorder();
    await recorder.start();
    state.recorder = recorder;
    record.textContent = "Terminer l'enregistrement";
    record.disabled = false;
    let remaining = MAX_SECONDS;
    el("enroll-timer").textContent = remaining + " s";
    state.countdown = setInterval(() => {
      remaining -= 1;
      if (el("enroll-timer")) el("enroll-timer").textContent = Math.max(remaining, 0) + " s";
      if (remaining <= 0) clearInterval(state.countdown);
    }, 1000);
    setTimeout(() => { if (state.recorder === recorder) toggleRecording(); }, MAX_SECONDS * 1000);
  } catch (error) {
    state.recorder = null;
    record.disabled = false;
    status("Micro indisponible : " + error.message, "error");
  }
}

async function upload(blob) {
  const session = state.enrollment;
  if (!session) return;
  clearInterval(state.countdown);
  el("enroll-timer").textContent = "";
  el("enroll-record").textContent = "Enregistrer ce passage";
  status("Calcul de l'empreinte vocale…", "");
  try {
    const result = await api("/api/profiles/" + session.profile.id + "/enroll", {
      method: "POST",
      headers: { "Content-Type": "audio/wav" },
      body: blob,
    });
    session.step += 1;
    session.profile.samples = result.samples;
    await refresh();
    if (session.step >= PHRASES.length * PASSAGES) {
      status("Enrôlement terminé : " + result.samples + " échantillons conservés sur ce PC.", "good");
      state.enrollment = null;
      renderEnrollment();
    } else {
      status("Passage enregistré (" + result.duration_seconds + " s). Continuez.", "good");
      renderEnrollment();
    }
  } catch (error) {
    status(error.message, "error");
  }
}

async function playLast(profile) {
  try {
    const data = await api("/api/profiles/" + profile.id + "/samples");
    const last = data.items[data.items.length - 1];
    if (!last) { status("Aucun échantillon à réécouter.", "error"); return; }
    const audio = el("profile-preview");
    audio.src = "/api/profiles/" + profile.id + "/samples/" + last.audio_file;
    await audio.play();
  } catch (error) {
    status(error.message, "error");
  }
}

async function removeProfile(profile) {
  const confirmed = window.confirm("Supprimer le profil « " + profile.name + " » et tous ses échantillons audio ?");
  if (!confirmed) return;
  try {
    await api("/api/profiles/" + profile.id, { method: "DELETE" });
    if (state.enrollment?.profile.id === profile.id) {
      state.enrollment = null;
      renderEnrollment();
    }
    await refresh();
    status("Profil supprimé, audio compris.", "good");
  } catch (error) {
    status(error.message, "error");
  }
}

async function refresh() {
  const [data,identity] = await Promise.all([api("/api/profiles"),api("/api/voice-identity/status")]);
  state.profiles = data.items;
  state.model = data.model;
  state.speakerReady = Boolean(data.speaker?.available);
  state.identity=identity;
  el("identity-calibrate").disabled=!state.speakerReady || identity.complete_profiles < 2 || (identity.profiles < 2);
  el("identity-state").textContent=identity.state==="ready"?"Reconnaissance expérimentale activée : elle ne remplace pas une authentification.":identity.state==="tests_required"?"Calibration prête : chaque personne doit faire deux nouveaux essais au micro.":"Calibration inactive : au moins deux personnes avec six échantillons sont nécessaires.";
  render();
}

async function testIdentity(profile) {
  if(state.recorder) {status("Un enregistrement est déjà en cours.","error");return;}
  try {
    const recorder=new Recorder(); await recorder.start();state.recorder=recorder;render();
    status("Parlez naturellement pendant six secondes pour tester votre voix.");
    await new Promise(resolve=>setTimeout(resolve,6000));
    const blob=await recorder.stop();state.recorder=null;
    const calibrated=state.identity?.state==="tests_required" || state.identity?.state==="ready";
    const path=calibrated?"/api/voice-identity/probe/"+profile.id:"/api/profiles/identify";
    const result=await api(path,{method:"POST",headers:{"Content-Type":"audio/wav"},body:blob});
    await refresh();
    if(calibrated) status(result.match?(result.validated?"Essai réussi. Reconnaissance expérimentale activée.":"Essai réussi. Il reste "+result.remaining+" essai(s) pour ce profil."):result.message,result.match?"good":"error");
    else status(result.best?.profile_id===profile.id?"Voix ressemblante dans ce test, mais identité non validée : une autre voix est nécessaire.":"Voix non reconnue dans ce test indicatif. La calibration reste inactive.",result.best?.profile_id===profile.id?"good":"error");
  } catch(error) {state.recorder?.close();state.recorder=null;status(error.message,"error");render();}
}

async function createProfile(event) {
  event.preventDefault();
  const name = el("profile-name").value.trim();
  const role = el("profile-role").value;
  if (!name) return;
  try {
    await api("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, role }),
    });
    el("profile-name").value = "";
    await refresh();
    status("Profil créé. Enregistrez maintenant trois phrases, deux fois chacune.", "good");
  } catch (error) {
    status(error.message, "error");
  }
}

function bind() {
  if (!el("profiles-list")) return;
  el("profile-form")?.addEventListener("submit", createProfile);
  el("enroll-record")?.addEventListener("click", toggleRecording);
  el("enroll-cancel")?.addEventListener("click", () => {
    if (state.recorder) { state.recorder.close(); state.recorder = null; }
    clearInterval(state.countdown);
    state.enrollment = null;
    renderEnrollment();
  });
  el("identity-calibrate")?.addEventListener("click",async()=>{
    try { await api("/api/voice-identity/calibrate",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}); await refresh(); status("Calibration préparée. Chaque personne doit faire deux essais indépendants."); }
    catch(error) {status(error.message,"error");}
  });
  refresh().catch((error) => status(error.message, "error"));
}

bind();

