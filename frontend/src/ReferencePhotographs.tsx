import pressure from './assets/reference-photos/digital-pressure-meter.jpg';
import valves from './assets/reference-photos/household-valves.jpg';

export const referencePhotographs = [
  { name: 'Digital pressure meter', image: pressure, credit: 'Nick.follows',
    source: 'https://commons.wikimedia.org/wiki/File:C9557_01_1200_RGB_300dpi.jpg',
    description: 'A real instrument with pressure ports and a digital display. This photograph does not establish the connected measurement mode or the identity F-17.' },
  { name: 'Household ball valves', image: valves, credit: 'NVgt156',
    source: 'https://commons.wikimedia.org/wiki/File:Ball_valve_in_household.jpg',
    description: 'Real valves and visible pipework. External handle orientation does not establish internal condition or the identity V-08.' },
];

export function ReferencePhotographs() {
  return <details className="reference-photographs"><summary>Real photograph examples and credits</summary>
    <p>Use your own photograph for an assigned task. These public reference photographs are not from this simulated plant and do not satisfy its evidence checklist. No example is submitted automatically.</p>
    <div className="photo-reference-grid">{referencePhotographs.map(photo => <figure key={photo.name}>
      <img src={photo.image} alt={photo.name} loading="lazy" />
      <figcaption><strong>{photo.name}</strong><p>{photo.description}</p>
        <p>Photo: {photo.credit} · <a href={photo.source} target="_blank" rel="noreferrer">Original and attribution</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a>. Wikimedia thumbnail; no application edits.</p>
        <a className="button secondary" href={photo.image} download>Download reference photograph</a>
      </figcaption>
    </figure>)}</div>
  </details>;
}
