const musicEl = id => document.getElementById(id);

async function musicApi(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Commande musicale impossible.");
  return result;
}

function musicFeedback(text) {
  musicEl("music-feedback").textContent = text;
}

function showMusicStatus(status) {
  const state = musicEl("music-state");
  state.textContent = status.configured ? "Lecteur configuré" : "Lecteur à choisir";
  musicEl("music-player-status").textContent = status.configured
    ? `Lecteur : ${status.configured_player || status.player_entity_id}${status.current?.state ? ` · ${status.current.state}` : ""}${status.current?.media_title ? ` · ${status.current.media_title}` : ""}`
    : "Aucun lecteur Music Assistant n’est encore sélectionné.";
  if (status.player_entity_id) musicEl("music-player").value = status.player_entity_id;
  if (status.duck_percent) musicEl("music-duck-percent").value = status.duck_percent;
  if (status.default_playlist?.uri) musicEl("music-playlist").value = status.default_playlist.uri;
}

let musicPlaylists = [];

function renderMusicPlaylists(selected) {
  const search = musicEl("music-playlist-search").value.trim().toLocaleLowerCase("fr");
  const select = musicEl("music-playlist");
  const previous = selected || select.value;
  select.replaceChildren(new Option("Aucune playlist par défaut", ""));
  for (const item of musicPlaylists.filter(item => !search || `${item.name} ${item.provider}`.toLocaleLowerCase("fr").includes(search))) {
    select.add(new Option(`${item.name} · ${item.provider}`, item.uri));
  }
  if (previous) select.value = previous;
}

async function refreshMusicPlaylists(selected) {
  try {
    const result = await musicApi("/api/music/playlists");
    musicPlaylists = result.items;
    renderMusicPlaylists(selected || result.selected?.uri || "");
  } catch(error) { musicFeedback(error.message); }
}

async function refreshMusicStatus() {
  try {
    const [config, players] = await Promise.all([musicApi("/api/music/config"), musicApi("/api/music/players")]);
    const previous = config.player_entity_id || musicEl("music-player").value;
    musicEl("music-player").replaceChildren(
      new Option("Choisir un lecteur", ""),
      ...players.items.map(player => new Option(`${player.name} · ${player.entity_id}`, player.entity_id))
    );
    if (previous) musicEl("music-player").value = previous;
    showMusicStatus(config);
    refreshMusicPlaylists(config.default_playlist?.uri || "");
  } catch(error) {
    musicEl("music-state").textContent = "Configuration indisponible";
    musicFeedback(error.message);
  }
}

musicEl("music-config").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const uri = musicEl("music-playlist").value;
    const chosen = musicPlaylists.find(item => item.uri === uri);
    const current = await musicApi("/api/music/config");
    const status = await musicApi("/api/music/config", {
      entity_id:musicEl("music-player").value,
      duck_percent:Number(musicEl("music-duck-percent").value),
      default_playlist:chosen || (current.default_playlist?.uri === uri ? current.default_playlist : null),
      clear_playlist:!uri
    });
    showMusicStatus(status);
    musicFeedback("Lecteur musical enregistré.");
  } catch(error) { musicFeedback(error.message); }
  finally { button.disabled = false; }
});

musicEl("music-playlist-search").addEventListener("input", () => renderMusicPlaylists());

musicEl("music-play").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const result = await musicApi("/api/music/play", {
      query:musicEl("music-query").value.trim(), media_type:musicEl("music-type").value
    });
    musicFeedback(result.message);
  } catch(error) { musicFeedback(error.message); }
  finally { button.disabled = false; }
});

for (const button of document.querySelectorAll("[data-music-control]")) {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      const result = await musicApi("/api/music/control", {action:button.dataset.musicControl});
      musicFeedback(result.message);
    } catch(error) { musicFeedback(error.message); }
    finally { button.disabled = false; }
  });
}

refreshMusicStatus();
