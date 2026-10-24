export function Icon({ name, size = 20 }: { name: 'trace' | 'grid' | 'phone' | 'arrow' | 'reset' | 'eye' | 'check' | 'close'; size?: number }) {
  const paths = {
    trace: 'M3 15h4l3-9 4 14 3-9h4', grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    phone: 'M8 2h8a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z M11 18h2',
    arrow: 'M4 12h16 M14 6l6 6-6 6', reset: 'M4 9a8 8 0 1 1 0 7 M4 3v6h6',
    eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
    check: 'M5 12l4 4L20 5', close: 'M6 6l12 12 M18 6 6 18',
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
