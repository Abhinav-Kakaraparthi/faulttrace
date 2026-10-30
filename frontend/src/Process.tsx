import { equipment, type Equipment } from './demo';

export function Process({ active, selected, onSelect, readings }: { active: boolean; selected: Equipment; onSelect: (id: Equipment) => void; readings?: { pressure: number | null; valve: number | null } }) {
  const select = (id: Equipment) => ({ role: 'button' as const, tabIndex: 0,
    'aria-label': `Inspect ${id} ${equipment[id].name}`, 'aria-pressed': selected === id,
    onClick: () => onSelect(id), onKeyDown: (event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(id); }
    },
  });
  return <section className="process section-surface" aria-labelledby="process-title">
    <div className="section-heading"><div><h2 id="process-title">Process overview</h2></div><span className="quiet-label">{readings ? 'Illustrative topology / stored measurements' : 'Schematic / sample'}</span></div>
    <div className="schematic-wrap" tabIndex={0} role="region" aria-label="Scrollable P-04 F-17 V-08 process schematic"><svg className="schematic" viewBox="0 0 750 240" aria-label="Cooling return line from pump P-04 through filter F-17 and valve V-08">
      <defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#293438" /></pattern></defs>
      <rect width="750" height="260" fill="url(#dots)" />
      <path d="M35 126H715 M75 126V205H680V126" fill="none" stroke="#425b5e" strokeWidth="4" />
      <path d="m56 121 9 5-9 5 m210-10 9 5-9 5 m210-10 9 5-9 5 m210-10 9 5-9 5" fill="none" stroke="#73c7bd" strokeWidth="2" />
      <text x="25" y="20" className="svg-small">RETURN LINE</text><text x="540" y="225" className="svg-small">TO COOLING CIRCUIT →</text>
      <g {...select('P-04')} className={`equipment ${selected === 'P-04' ? 'selected' : ''}`}>
        <rect className="equipment-hit" x="108" y="72" width="118" height="105" rx="12" />
        <circle cx="167" cy="126" r="29" className="equipment-body" /><path d="m152 110 33 16-33 16z" fill="#70beb4" />
        <text x="167" y="40" textAnchor="middle" className="svg-id">P-04</text><text x="167" y="63" textAnchor="middle" className="svg-small">Circulation pump</text>
        <text x="167" y="196" textAnchor="middle" className="svg-small">{readings ? 'Not observed' : 'RUNNING'}</text>
      </g>
      <g {...select('F-17')} className={`equipment ${selected === 'F-17' ? 'selected' : ''}`}>
        <rect className="equipment-hit" x="305" y="72" width="120" height="105" rx="12" />
        <rect x="338" y="99" width="55" height="54" rx="4" className="equipment-body" />
        <path d="m342 146 43-43 m-32 46 36-36 m-48 19 29-29" stroke="#70beb4" strokeWidth="2" />
        <path d="M345 98V82h40v16" stroke="#8da7aa" fill="none" strokeWidth="2" />
        <text x="365" y="40" textAnchor="middle" className="svg-id">F-17</text><text x="365" y="63" textAnchor="middle" className="svg-small">Return-line filter</text>
        <text x="365" y="196" textAnchor="middle" className={active && !readings ? 'svg-amber' : 'svg-small'}>{readings ? (readings.pressure === null ? 'Pressure unavailable' : `${readings.pressure} kPa / simulated`) : active ? '184 kPa / ELEVATED' : '62 kPa / BASELINE'}</text>
      </g>
      <g {...select('V-08')} className={`equipment ${selected === 'V-08' ? 'selected' : ''}`}>
        <rect className="equipment-hit" x="513" y="72" width="118" height="105" rx="12" />
        <path d="m544 109 48 34v-34l-48 34z" className="equipment-body" /><path d="M568 109V88m-15 0h30" stroke="#70beb4" strokeWidth="3" />
        <text x="568" y="40" textAnchor="middle" className="svg-id">V-08</text><text x="568" y="63" textAnchor="middle" className="svg-small">Control valve</text>
        <text x="568" y="196" textAnchor="middle" className="svg-small">{readings ? (readings.valve === null ? 'Feedback unavailable' : `${readings.valve}% / simulated`) : '72% FEEDBACK'}</text>
      </g>
    </svg></div>
    <div className="equipment-selector" aria-label="Select equipment">{(Object.keys(equipment) as Equipment[]).map(id => <button key={id} aria-pressed={selected === id} onClick={() => onSelect(id)}><strong>{id}</strong><span>{equipment[id].name}</span></button>)}</div>
    <div className="equipment-detail"><span className="equipment-tag">{selected}</span><div><strong>{equipment[selected].name}</strong><details className="equipment-context"><summary>Equipment details</summary><p>{equipment[selected].detail}</p></details></div><span className="quiet-label">Observation only</span></div>
  </section>;
}

export function Telemetry({ active }: { active: boolean }) {
  return <section className="telemetry section-surface" aria-labelledby="telemetry-title">
    <div className="section-heading"><div><h2 id="telemetry-title">Differential-pressure trend</h2></div><span className="chart-legend"><i /> Differential pressure</span></div>
    <div className="chart-scroll"><svg className="chart" viewBox="0 0 740 205" role="img" aria-label={active ? 'Sample differential pressure rises from 62 to 184 kilopascals over 20 minutes.' : 'Baseline sample differential pressure stays near 62 kilopascals.'}>
      <text x="15" y="16" className="svg-small">kPa</text>
      {[40, 90, 140].map((y, i) => <g key={y}><path d={`M53 ${y}H715`} stroke="#2d393d" strokeDasharray="3 5" /><text x="12" y={y + 5} className="svg-small">{200 - i * 75}</text></g>)}
      <path d={active ? 'M54 135 120 134 185 136 250 130 315 126 380 104 445 83 510 69 575 58 640 54 714 51' : 'M54 135 120 134 185 136 250 133 315 135 380 132 445 134 510 135 575 132 640 134 714 133'} fill="none" stroke="#63d6c4" strokeWidth="3" strokeLinejoin="round" />
      {active && <><path d="M380 25V160" stroke="#b6a06b" strokeDasharray="4 4" /><text x="393" y="28" className="svg-amber">Sample incident</text><circle cx="714" cy="51" r="5" fill="#63d6c4" /></>}
      {[['−20 min', 54], ['−15 min', 218], ['−10 min', 382], ['−5 min', 548], ['Now', 693]].map(([label, x]) => <text key={label} x={x} y="186" className="svg-small">{label}</text>)}
    </svg></div><p className="caption">Fixed sample series · not a live sensor connection<span className="mobile-hint">Scroll the chart horizontally to inspect all sample times.</span></p>
  </section>;
}
