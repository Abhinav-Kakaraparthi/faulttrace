export type Profile = 'release' | 'local' | 'demo';
export type Identity = {
  profile: Profile; principal_id: string | null; role: 'commander' | 'operator' | null;
  capabilities: { create_incident: boolean }; incident_ids: string[];
};
export function configuredProfile(value: unknown): Profile {
  if (value === undefined || value === '' || value === 'release') return 'release';
  if (value === 'local') return 'local';
  throw new Error('Invalid access profile configuration. Use release or explicit local.');
}
function fields(value: unknown, expected: string[]): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).sort().join(',') === expected.sort().join(',');
}
export function validateIdentity(value: unknown, profile: Profile): Identity {
  const invalid = () => { throw new Error('Server identity does not match the configured access profile. Access remains closed.'); };
  if (!fields(value, ['profile', 'principal_id', 'role', 'capabilities', 'incident_ids'])) return invalid();
  if (value.profile !== profile || !fields(value.capabilities, ['create_incident']) ||
      typeof value.capabilities.create_incident !== 'boolean' || !Array.isArray(value.incident_ids) ||
      !value.incident_ids.every(id => typeof id === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id)) ||
      new Set(value.incident_ids).size !== value.incident_ids.length) return invalid();
  if (profile === 'local') {
    if (value.principal_id !== null || value.role !== null || value.capabilities.create_incident || value.incident_ids.length) return invalid();
  } else if (typeof value.principal_id !== 'string' || !value.principal_id.trim() ||
      !['commander', 'operator'].includes(value.role as string) ||
      (value.role === 'operator' && value.capabilities.create_incident)) return invalid();
  if (profile === 'demo' && value.capabilities.create_incident) return invalid();
  return value as Identity;
}
export function canCreate(identity: Identity): boolean {
  return identity.profile === 'local' || (identity.role === 'commander' && identity.capabilities.create_incident);
}
export function workspaceAllowed(identity: Identity, workspace: string): boolean {
  return identity.profile === 'local' || identity.role === workspace;
}
