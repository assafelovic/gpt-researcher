export const backendUrl = () =>
  process.env.GPTR_API_URL ||
  process.env.NEXT_PUBLIC_GPTR_API_URL ||
  'http://localhost:8000';

export const backendHeaders = (headers: Record<string, string> = {}) => {
  const apiKey = process.env.API_AUTH_KEY;
  return {
    ...headers,
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
  };
};
