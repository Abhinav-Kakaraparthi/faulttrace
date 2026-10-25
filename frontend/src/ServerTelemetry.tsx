import type { Sample } from './journeyState';

export function ServerTelemetry({ samples }: { samples: Sample[] }) {
  if (!samples.length) return <section className="section-surface server-telemetry"><h2>Telemetry</h2><p>No timestamped simulator measurements are available for this incident. No sample-preview readings are substituted.</p></section>;
  const latest = samples.at(-1)!;
  const origin = Date.parse(samples[0].timestamp);
  const elapsed = (s: Sample) => (Date.parse(s.timestamp) - origin) / 1000;
  const duration = Math.max(0, elapsed(latest));
  const max = Math.max(50, Math.ceil(Math.max(...samples.map(s => s.pressure)) / 50) * 50);
  const x = (s: Sample) => 65 + elapsed(s) / Math.max(1, duration) * 600;
  const y = (s: Sample) => 160 - s.pressure / max * 130;
  return <section className="section-surface server-telemetry"><h2>Stored simulated telemetry</h2>
    <div className="journey-metrics"><div><span>Return flow</span><strong>{latest.flow} <small>m3/h</small></strong></div><div><span>Differential pressure</span><strong>{latest.pressure} <small>kPa</small></strong></div><div><span>Valve feedback</span><strong>{latest.valve}<small>%</small></strong></div><div><span>Active alarm</span><strong className="journey-alarm">{latest.alarm ?? 'None'}</strong></div></div>
    <div className="chart-scroll" tabIndex={0} role="region" aria-label="Scrollable stored telemetry chart">
      <svg viewBox="0 0 740 225" className="chart" role="img" aria-label={`${samples.length} stored simulated pressure measurements; latest ${latest.pressure} kPa. Full values are in the evidence table.`}>
        <text x="12" y="18" className="svg-small">kPa</text>
        {[0, max / 2, max].map(value => <g key={value}><line x1="65" y1={160-value/max*130} x2="665" y2={160-value/max*130} stroke="#3d5057" /><text x="12" y={165-value/max*130} className="svg-small">{value}</text></g>)}
        <polyline points={samples.map(s => `${x(s)},${y(s)}`).join(' ')} fill="none" stroke="#76ddca" strokeWidth="3" />
        {samples.map(s => <circle key={s.id} cx={x(s)} cy={y(s)} r="3" fill="#b1f0df"><title>{s.timestamp}: {s.pressure} kPa</title></circle>)}
        <text x="65" y="187" className="svg-small">0</text>{duration > 0 && <text x="635" y="187" className="svg-small">{duration}</text>}
        <text x="200" y="214" className="svg-small">Simulated seconds from first stored sample</text>
      </svg>
    </div><p className="caption">Simulated measurement time (UTC): <time dateTime={latest.timestamp}>{latest.timestamp}</time>. Explicit clock steps; no real sensor connection. Full source values remain in the evidence table.</p>
  </section>;
}
