interface GetHostParams {
  purpose?: string;
}

export const getHost = ({ purpose }: GetHostParams = {}): string => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    const apiUrl = localStorage.getItem("GPTR_API_URL");
    const urlParams = new URLSearchParams(window.location.search);
    const urlApiUrl = urlParams.get("GPTR_API_URL");
    if (urlApiUrl) {
      return urlApiUrl;
    } else if (apiUrl) {
      return apiUrl;
    } else if (process.env.NEXT_PUBLIC_GPTR_API_URL) {
      return process.env.NEXT_PUBLIC_GPTR_API_URL;
    } else if (purpose === 'langgraph-gui') {
      return host.includes('localhost') ? 'http%3A%2F%2F127.0.0.1%3A8123' : `https://${host}`;
    } else {
      return host.includes('localhost') ? 'http://localhost:8000' : `https://${host}`;
    }
  }
  return '';
};