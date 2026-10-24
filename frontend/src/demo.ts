export type View = 'commander' | 'operator';
export type Equipment = 'P-04' | 'F-17' | 'V-08';
export type Outcome = 'readable' | 'unreadable' | 'cannot-access' | 'wrong-equipment';
export type Evidence = { id: number; outcome: Outcome; fixture?: 'a' | 'b'; note: string };
export type Activity = { title: string; detail: string; evidence?: number };
export type Demo = { started: boolean; waiting: boolean; evidence: Evidence[]; activity: Activity[] };
export type Action = { type: 'start' | 'reset' | 'reopen' } | { type: 'submit'; outcome: Outcome; fixture?: 'a' | 'b'; note: string };
export const initial: Demo = { started: false, waiting: false, evidence: [], activity: [] };
export const outcomeLabels: Record<Outcome, string> = {
  readable: 'Readable observation', unreadable: 'Unreadable evidence',
  'cannot-access': 'Cannot access', 'wrong-equipment': 'Wrong equipment',
};
export const equipment: Record<Equipment, { name: string; detail: string }> = {
  'P-04': { name: 'Circulation pump', detail: 'Sample motor state: running. Local pump condition has not been inspected.' },
  'F-17': { name: 'Return-line filter', detail: 'Assigned observation: read the local differential-pressure indicator. Asset identity is task-assigned, not proven by the image.' },
  'V-08': { name: 'Flow control valve', detail: 'Sample position feedback: 72%. Feedback alone does not prove the physical valve position.' },
};
export function reduceDemo(state: Demo, action: Action): Demo {
  if (action.type === 'reset') return initial;
  if (action.type === 'start') return state.started ? state : {
    ...initial, started: true, waiting: true, activity: [
      { title: 'Sample incident started', detail: 'Flow decreased while filter differential pressure increased.' },
      { title: 'Local observation requested', detail: 'Read the F-17 indicator before choosing an explanation.' },
    ],
  };
  if (action.type === 'reopen') return !state.started || state.waiting ? state : {
    ...state, waiting: true,
    activity: [...state.activity, { title: 'Observation requested again', detail: 'Earlier evidence remains in the investigation record.' }],
  };
  if (action.type !== 'submit' || !state.started || !state.waiting) return state;
  const evidence: Evidence = { id: state.evidence.length + 1, outcome: action.outcome, fixture: action.fixture, note: action.note.trim() };
  return { ...state, waiting: false, evidence: [...state.evidence, evidence], activity: [...state.activity, {
    title: outcomeLabels[action.outcome], evidence: evidence.id,
    detail: action.outcome === 'readable' ? 'Synthetic local indicator: 180 kPa. A sample observation, not a diagnosis.'
      : action.outcome === 'unreadable' ? 'No numeric reading recorded. Another observation is needed.'
      : action.outcome === 'wrong-equipment' ? 'Asset identity disputed. Confirm the location before proceeding.'
      : 'Access blocked. No equipment observation was made.',
  }] };
}
