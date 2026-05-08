interface GetHostParams {
  purpose?: string;
}

const normalizeBackendUrl = (value?: string | null): string => {
  if (!value) {
    return '';
  }

  return value
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/api$/, '');
};

export const getHost = ({ purpose }: GetHostParams = {}): string => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    const apiUrlInLocalStorage = normalizeBackendUrl(localStorage.getItem("GPTR_API_URL"));
    
    const urlParams = new URLSearchParams(window.location.search);
    const apiUrlInUrlParams = normalizeBackendUrl(urlParams.get("GPTR_API_URL"));
    
    if (apiUrlInLocalStorage) {
      return apiUrlInLocalStorage;
    } else if (apiUrlInUrlParams) {
      return apiUrlInUrlParams;
    } else if (process.env.NEXT_PUBLIC_GPTR_API_URL) {
      return normalizeBackendUrl(process.env.NEXT_PUBLIC_GPTR_API_URL);
    } else if (process.env.REACT_APP_GPTR_API_URL) {
      return normalizeBackendUrl(process.env.REACT_APP_GPTR_API_URL);
    } else if (purpose === 'langgraph-gui') {
      return host.includes('localhost') ? 'http%3A%2F%2F127.0.0.1%3A8123' : `https://${host}`;
    } else {
      return host.includes('localhost') ? 'http://localhost:8002' : `https://${host}`;
    }
  }
  return '';
};
