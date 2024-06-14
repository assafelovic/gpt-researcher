export const getHost = () => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    return host.includes('localhost') ? 'http://localhost:8000' : `https://${host}`;
  }
  return '';
};

