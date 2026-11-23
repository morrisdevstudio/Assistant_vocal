import { useEffect, useRef, useState } from 'react'
import { Disc3, Heart, ListMusic, Minus, Music2, Pause, Play, Plus, Search, SkipBack, SkipForward, Speaker, Square, X } from 'lucide-react'
import { musicCategories } from './preferences'
import type { MusicCategory } from './preferences'
import { backendJson, jsonPost, useRemote, useServerAction } from './backend'
import { clock } from './schedule-model'

const mediaTypes = { Artistes: 'artist', Albums: 'album', Titres: 'track', Playlists: 'playlist' }
type MusicStatus = {
  configured: boolean
  player_entity_id: string | null
  configured_player: string | null
  error?: string
  current: { state: string; media_title: string | null; media_album_name: string | null; media_artist: string | null;
    media_duration: number | null; media_position: number | null; media_position_updated_at: string | null;
    supported_features: number | null; artwork_url?: string } | null
}
type MusicPlayers = { items: { entity_id: string; name: string; state: string }[]; selected: string | null }

function MusicArtwork({ url }: { url?: string }) {
  const [failed, setFailed] = useState(false)
  return <div className="music-artwork">
    {url && !failed ? <img src={url} alt="Pochette du morceau" onError={() => setFailed(true)} />
      : <div role="img" aria-label="Aucune pochette disponible"><Disc3 size={76} strokeWidth={0.8} aria-hidden="true" /></div>}
  </div>
}

export function MusicPage({ active, defaultCategory, selectedPlayer, onSelectPlayer }: {
  active: boolean
  defaultCategory: MusicCategory
  selectedPlayer: string
  onSelectPlayer: (player: string) => boolean
}) {
  const [query, setQuery] = useState('')
  const [selection, setSelection] = useState({ preference: defaultCategory, category: defaultCategory })
  const category = selection.preference === defaultCategory ? selection.category : defaultCategory
  if (selection.preference !== defaultCategory) setSelection({ preference: defaultCategory, category: defaultCategory })
  const search = useRef<HTMLInputElement>(null)
  const searching = !!query.trim()
  const [now, setNow] = useState(Date.now)
  const [seekTo, setSeekTo] = useState<number | null>(null)
  const [notice, setNotice] = useState('')
  const [selectionError, setSelectionError] = useState('')
  // Les métadonnées du sélecteur changent peu et HA renvoie tous ses états.
  const players = useRemote<MusicPlayers>(active ? 'music/players?music_assistant_only=true' : null, 60000)
  const statusPath = selectedPlayer ? 'music/config?' + new URLSearchParams({ entity_id: selectedPlayer }) : 'music/config'
  const status = useRemote<MusicStatus>(active ? statusPath : null, 5000)
  const defaultPlayer = players.data?.selected
  const defaultName = players.data?.items.find(player => player.entity_id === defaultPlayer)?.name
    ?? (!selectedPlayer ? status.data?.configured_player : defaultPlayer)
  const library = useRemote<{ items: { uri: string; name: string }[] }>(active
    ? 'music/library?' + new URLSearchParams({ media_type: mediaTypes[category], query: query.trim() }) : null,
    0, searching ? 350 : 0)
  const server = useServerAction()
  const current = status.data?.current
  const playing = current?.state === 'playing'
  const canPlay = !!current && !['unavailable', 'unknown'].includes(current.state)
  const ready = canPlay && current.state !== 'off'
  const duration = current?.media_duration ?? 0
  const elapsed = playing && current.media_position_updated_at ? (now - Date.parse(current.media_position_updated_at)) / 1000 : 0
  const position = Math.min(duration, Math.max(0, (current?.media_position ?? 0) + (Number.isFinite(elapsed) ? elapsed : 0)))
  const canSeek = !!(duration && ((current?.supported_features ?? 0) & 2))

  useEffect(() => {
    if (!active || !playing) return
    function tick() { if (!document.hidden) setNow(Date.now()) }
    tick()
    const id = window.setInterval(tick, 1000)
    document.addEventListener('visibilitychange', tick)
    return () => {
      window.clearInterval(id)
      document.removeEventListener('visibilitychange', tick)
    }
  }, [active, playing])

  async function command(path: 'control' | 'play', body: Record<string, string | number>) {
    const entityId = status.data?.player_entity_id
    if (!entityId) return
    setNotice('')
    const result = await server.run(() => backendJson<{ message: string }>('music/' + path,
      jsonPost({ ...body, entity_id: entityId })))
    status.reload()
    if (result) setNotice(result.message)
  }

  function seek() {
    if (seekTo === null) return
    const position = seekTo
    setSeekTo(null)
    void command('control', { action: 'seek', position })
  }

  return <section className="music-page" hidden={!active} aria-labelledby="music-heading">
    <div className="music-content">
      <h1 id="music-heading" className="sr-only">Musique</h1>
      <div className="music-player">
        <label className="music-player-select">
          <Speaker size={17} strokeWidth={1.6} aria-hidden="true" />
          <span className="sr-only">Lecteur de diffusion</span>
          <select value={selectedPlayer} disabled={server.busy || !players.data} onChange={event => {
            setSeekTo(null)
            setNotice('')
            setSelectionError(onSelectPlayer(event.target.value) ? '' : 'Impossible de mémoriser le lecteur sur cet appareil.')
          }}>
            <option value="">{defaultName ? `Par défaut · ${defaultName}` : 'Choisir un lecteur'}</option>
            {selectedPlayer && !players.data?.items.some(player => player.entity_id === selectedPlayer) &&
              <option value={selectedPlayer} disabled>{status.data?.configured_player || selectedPlayer}</option>}
            {players.data?.items.map(player => <option key={player.entity_id} value={player.entity_id}
              disabled={['unavailable', 'unknown'].includes(player.state)}>{player.name}</option>)}
          </select>
        </label>
        <MusicArtwork key={current?.artwork_url} url={current?.artwork_url} />
        <div className="music-track">
          <h2>{current?.media_title || 'Aucun titre en cours'}</h2>
          {(current?.media_album_name || current?.media_artist) && <p>{[current.media_album_name, current.media_artist].filter(Boolean).join(' · ')}</p>}
        </div>
        <div className="music-progress">
          <label className="sr-only" htmlFor="music-position">Position dans le morceau</label>
          <input id="music-position" type="range" min="0" max={duration || 1} value={seekTo ?? position} step="1" disabled={!ready || !canSeek || server.busy}
            onChange={event => setSeekTo(Number(event.target.value))} onPointerUp={seek} onKeyUp={seek} onBlur={seek} />
          <div className="music-times" aria-hidden="true"><span>{duration ? clock((seekTo ?? position) * 1000) : '—:—'}</span><span>{duration ? clock(duration * 1000) : '—:—'}</span></div>
        </div>
        <div className="music-playback" role="group" aria-label="Lecture">
          <button type="button" className="music-round-button" disabled={!ready || server.busy} aria-label="Morceau précédent" onClick={() => void command('control', { action: 'previous' })}><SkipBack size={24} strokeWidth={1.6} /></button>
          <button type="button" className="music-round-button music-play-button" disabled={!ready || server.busy} aria-label={playing ? 'Mettre en pause' : 'Reprendre la lecture'} onClick={() => void command('control', { action: playing ? 'pause' : 'resume' })}>{playing ? <Pause size={31} strokeWidth={1.5} /> : <Play size={31} strokeWidth={1.5} />}</button>
          <button type="button" className="music-round-button" disabled={!ready || server.busy} aria-label="Morceau suivant" onClick={() => void command('control', { action: 'next' })}><SkipForward size={24} strokeWidth={1.6} /></button>
        </div>
        <div className="music-volume" role="group" aria-label="Volume et arrêt">
          <button type="button" className="music-round-button" disabled={!ready || server.busy} aria-label="Baisser le volume" onClick={() => void command('control', { action: 'volume_down' })}><Minus size={21} strokeWidth={1.6} /></button>
          <button type="button" className="music-round-button" disabled={!ready || server.busy} aria-label="Arrêter la lecture" onClick={() => void command('control', { action: 'stop' })}><Square size={18} strokeWidth={1.6} /></button>
          <button type="button" className="music-round-button" disabled={!ready || server.busy} aria-label="Augmenter le volume" onClick={() => void command('control', { action: 'volume_up' })}><Plus size={21} strokeWidth={1.6} /></button>
        </div>
        <p id="music-connection-note" className="music-connection-note" role="status">{notice || (status.error ? 'Music Assistant indisponible' : !status.data ? 'Connexion à Music Assistant…' : canPlay ? 'Music Assistant' : 'Lecteur indisponible')}</p>
        {(selectionError || server.error || players.error || status.error || status.data?.error) && <p className="shopping-error" role="alert">{selectionError || server.error || players.error || status.error || status.data?.error}</p>}
      </div>

      <form className="music-search" role="search" onSubmit={event => event.preventDefault()}>
        <Search size={19} strokeWidth={1.7} aria-hidden="true" />
        <label className="sr-only" htmlFor="music-search-input">Rechercher de la musique</label>
        <input ref={search} id="music-search-input" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Rechercher de la musique…" maxLength={160} autoComplete="off" enterKeyHint="search" />
        {query && <button type="button" className="icon-button" aria-label="Effacer la recherche" onClick={() => { setQuery(''); search.current?.focus({ preventScroll: true }) }}><X size={18} /></button>}
      </form>

      <section className="music-library" aria-labelledby="music-library-heading">
        <div className="music-library-heading">
          {searching ? <Search size={17} strokeWidth={1.7} /> : <Heart size={17} strokeWidth={1.7} />}
          <h2 id="music-library-heading">{searching ? 'Résultats de recherche' : 'Vos favoris'}</h2>
        </div>
        <div className="music-categories" role="group" aria-label={searching ? 'Type de résultat' : 'Catégorie de favoris'}>
          {musicCategories.map(name => <button key={name} type="button" aria-pressed={category === name} className={category === name ? 'is-selected' : ''} onClick={() => setSelection({ preference: defaultCategory, category: name })}>{name}</button>)}
        </div>
        {library.error ? <p className="shopping-error" role="alert">{library.error}</p> : library.data?.items.length ?
          <ul className="house-items music-library-items">{library.data.items.map(({ uri, name }, index) => <li key={`${uri}-${index}`}><div><strong>{name}</strong></div>
            <button className="icon-button" type="button" disabled={!canPlay || server.busy} aria-label={`Lire ${name}`} onClick={() => void command('play', { query: uri, media_type: mediaTypes[category] })}><Play size={18} /></button>
          </li>)}</ul>
          : <div className="music-library-empty" role="status">
          {searching ? <Music2 size={29} strokeWidth={1.3} aria-hidden="true" /> : <ListMusic size={29} strokeWidth={1.3} aria-hidden="true" />}
          <p>{!library.data ? 'Chargement…' : searching ? 'Aucun résultat.' : 'Aucun favori dans cette catégorie.'}</p>
        </div>}
      </section>
    </div>
  </section>
}
