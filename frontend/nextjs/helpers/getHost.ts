interface GetHostParams {
  purpose?: string;
}

export const getHost = ({ purpose }: GetHostParams = {}): string => {
  // New simplified behavior: Always derive backend URL from current window location
  // Format: [protocol]//[hostname]:8000
  // Ignores localStorage, query params, and env vars per user request.
  if (typeof window === 'undefined') return '';

  try {
    const { protocol, hostname } = window.location;
    // Always target port 8000 regardless of current page port
    return `${protocol}//${hostname}:8000`;
  } catch (e) {
    // Fallback empty string if anything unexpected occurs (e.g. restricted environment)
    console.error('getHost error:', e);
    return '';
  }
};