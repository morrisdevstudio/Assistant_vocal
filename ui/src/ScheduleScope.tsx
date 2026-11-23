export function ScheduleScope({ label, local = false, onChange, busy = false }: {
  label: string
  local?: boolean
  onChange: () => void
  busy?: boolean
}) {
  return <div className="schedule-chips server-modes" role="group" aria-label="Emplacement">
    <button type="button" aria-pressed={!local} disabled={busy} onClick={() => { if (local) onChange() }}>{label}</button>
    <button type="button" aria-pressed={local} disabled={busy} onClick={() => { if (!local) onChange() }}>Sur cet appareil</button>
  </div>
}
