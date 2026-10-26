import type { Interpretation } from './api';

export type PhotoObservation = {
  category: 'gauge' | 'valve' | 'other' | 'cannot-determine'; readability: 'readable' | 'unreadable';
  measurement_type: 'pressure' | 'differential_pressure' | 'indeterminate' | 'unsupported' | 'not_applicable';
  visible_unit: string | null; reading: number | null; label_text: string | null;
  valve_orientation: 'parallel_to_visible_pipe' | 'perpendicular_to_visible_pipe' | 'intermediate' | 'indeterminate' | 'not_applicable';
  reasons: string[]; evidence_ref: string;
};
const reasons: Record<string, string> = {
  measurement_type_uncertain: 'Measurement type cannot be established from the photograph.',
  ambiguous_scale: 'Scale selection or reading is ambiguous; no number inferred.',
  unit_unreadable: 'Visible unit cannot be read; no number inferred.',
  unsupported_instrument: 'Instrument or unit is outside the supported observation contract.',
  image_unreadable: 'Relevant image evidence is unreadable.', category_uncertain: 'Image category cannot be determined.',
  not_equipment: 'Unrelated image; no equipment measurement applies.', orientation_uncertain: 'External handle orientation cannot be determined.',
  label_unreadable: 'Equipment label is missing, partial or unreadable.',
};
export function isPhotoObservation(value: Interpretation): value is PhotoObservation { return 'category' in value; }

export function PhotoInterpretation({ value, status }: { value: Interpretation; status: string }) {
  if (!isPhotoObservation(value)) return <section className="interpretation-block"><h4>NVIDIA interpretation / existing fixture DP-display contract</h4>
    <p>{value.readability === 'readable' ? `${value.reading} ${value.unit}` : 'Unreadable; reading and unit unknown.'}</p>
    <p>Instrument type and asset identity are not verified by this legacy contract.</p></section>;
  return <section className="interpretation-block" aria-label="NVIDIA photographic observation">
    <h4>NVIDIA photographic observation / {status}</h4>
    <dl className="evidence-provenance"><div><dt>Image category</dt><dd>{value.category}</dd></div>
      <div><dt>Observation readability</dt><dd>{value.readability}</dd></div>
      <div><dt>Model-reported measurement type</dt><dd>{value.measurement_type.replaceAll('_', ' ')}</dd></div>
      <div><dt>Observed numeric reading</dt><dd>{value.reading === null ? 'Not established; no number inferred' : value.reading}</dd></div>
      <div><dt>Visible unit / no conversion</dt><dd>{value.visible_unit ?? 'Not established / not applicable'}</dd></div>
      <div><dt>Visible label text / untrusted transcription</dt><dd><code>{value.label_text ?? 'Not established'}</code></dd></div>
      <div><dt>External handle orientation</dt><dd>{value.valve_orientation.replaceAll('_', ' ')}</dd></div>
      <div><dt>Source reference</dt><dd><code>{value.evidence_ref}</code></dd></div></dl>
    <h4>Uncertainty / bounded rejection reasons</h4>{value.reasons.length ? <ul>{value.reasons.map(code => <li key={code}>{reasons[code] ?? code}</li>)}</ul> : <p>No uncertainty code returned. This is not proof of measurement validity or accuracy.</p>}
    {status !== 'interpreted' && <p className="notice">Retained output is not an accepted current observation. Review analysis status and diagnostics.</p>}
    <p className="notice">Label text does not establish assigned asset identity. A model measurement type is not an independent compatibility check. Handle orientation does not prove internal valve position or operating condition.</p>
    <p>Observation only: excluded from incident pressure comparisons, planner conclusions and correction/recovery authorization pending explicit compatibility and evidence policy.</p>
  </section>;
}
