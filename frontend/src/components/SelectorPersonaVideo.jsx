export default function SelectorPersonaVideo({
  sessionData,
  selectedPersonaIdx,
  onSelect,
  candidateLabel = 'Person',
  selectedLabel = 'Selected',
  heading = 'Select the person executing the technique',
  subtitle,
  showCandidates = true,
}) {
  if (!sessionData) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ borderLeft: '3px solid var(--brand-red)', paddingLeft: '0.75rem' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 'bold', margin: '0 0 0.25rem 0' }}>{heading}</h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
          {subtitle || (sessionData.personas.length > 1
            ? `Detected ${sessionData.personas.length} persons.`
            : 'Confirm that the detected person is executing the technique.')}
        </p>
      </div>

      <div style={{ position: 'relative', width: '100%', borderRadius: '10px', overflow: 'hidden', background: '#000', border: '1px solid rgba(255,255,255,0.1)' }}>
        <img
          src={`data:image/jpeg;base64,${sessionData.frame_base64}`}
          alt="Initial video frame with detected persons"
          style={{ width: '100%', display: 'block', maxHeight: '420px', objectFit: 'contain' }}
        />
        {sessionData.personas.map((persona) => {
          const [x1, y1, x2, y2] = persona.bbox;
          const selected = selectedPersonaIdx === persona.idx;
          return (
            <button
              key={persona.idx}
              type="button"
              onClick={() => onSelect(persona.idx)}
              aria-label={`${candidateLabel} #${persona.idx}`}
              aria-pressed={selected}
              style={{
                position: 'absolute', left: `${(x1 / sessionData.frame_width) * 100}%`, top: `${(y1 / sessionData.frame_height) * 100}%`,
                width: `${((x2 - x1) / sessionData.frame_width) * 100}%`, height: `${((y2 - y1) / sessionData.frame_height) * 100}%`,
                border: selected ? '3px solid var(--brand-red)' : '2px dashed rgba(255,255,255,.8)',
                background: selected ? 'rgba(208,17,24,.28)' : 'rgba(0,0,0,.2)', color: 'white', cursor: 'pointer',
                borderRadius: '6px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '4px', boxSizing: 'border-box',
              }}
            >
              <span style={{ background: selected ? 'var(--brand-red)' : 'rgba(0,0,0,.75)', padding: '2px 6px', borderRadius: '4px', fontSize: '.72rem', fontWeight: 'bold' }}>
                {selected ? selectedLabel : `${candidateLabel} #${persona.idx}`}
              </span>
              <span style={{ background: 'rgba(0,0,0,.75)', padding: '2px 5px', borderRadius: '4px', fontSize: '.68rem' }}>
                {Math.round(persona.confianza * 100)}%
              </span>
            </button>
          );
        })}
      </div>

      {showCandidates && <div style={{ display: 'flex', gap: '.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        {sessionData.personas.map((persona) => {
          const selected = selectedPersonaIdx === persona.idx;
          return (
            <button
              key={persona.idx}
              type="button"
              onClick={() => onSelect(persona.idx)}
              aria-pressed={selected}
              className={selected ? 'btn-primary' : 'btn-secondary'}
            >
              {selected ? selectedLabel : `${candidateLabel} #${persona.idx}`} ({Math.round(persona.confianza * 100)}%)
            </button>
          );
        })}
      </div>}
    </div>
  );
}
