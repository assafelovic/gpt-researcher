const DEFAULT_PUBLIC_BACKEND_URL = 'http://localhost:8002';

export const normalizeBackendUrl = (value?: string | null): string => {
  if (!value) {
    return '';
  }

  return value
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/api$/, '');
};

const isDockerInternalBackendUrl = (value: string): boolean => {
  if (!value) {
    return false;
  }

  try {
    const parsed = value.includes('://') ? new URL(value) : new URL(`http://${value}`);
    return parsed.hostname === 'gpt-researcher';
  } catch {
    return (
      value === 'gpt-researcher' ||
      value.startsWith('gpt-researcher:') ||
      value.includes('://gpt-researcher')
    );
  }
};

export const sanitizeBrowserBackendUrl = (value?: string | null): string => {
  const normalized = normalizeBackendUrl(value);
  if (!normalized || isDockerInternalBackendUrl(normalized)) {
    return '';
  }

  return normalized;
};

export const resolveBrowserBackendUrl = (
  ...candidates: Array<string | undefined | null>
): string => {
  for (const candidate of candidates) {
    const normalized = sanitizeBrowserBackendUrl(candidate);
    if (normalized) {
      return normalized;
    }
  }

  return DEFAULT_PUBLIC_BACKEND_URL;
};

export const resolveServerBackendUrl = (
  ...candidates: Array<string | undefined | null>
): string => {
  for (const candidate of candidates) {
    const normalized = normalizeBackendUrl(candidate);
    if (normalized) {
      return normalized;
    }
  }

  return DEFAULT_PUBLIC_BACKEND_URL;
};
