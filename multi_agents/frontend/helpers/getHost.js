export const getHost = ({purpose} = {}) => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    if (purpose == 'langgraph-gui') {
      return host.includes('localhost') ? 'http%3A%2F%2F127.0.0.1%3A8123' : `https://${host}`;
    } else {
      return host.includes('localhost') ? 'http://localhost:8000' : `https://${host}`;
    }
  }
  return '';
};

