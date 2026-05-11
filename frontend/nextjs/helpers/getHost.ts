import {
  sanitizeBrowserBackendUrl,
} from './backendUrl';

interface GetHostParams {
  purpose?: string;
}

export const getHost = ({ purpose }: GetHostParams = {}): string => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    const apiUrlInLocalStorage = sanitizeBrowserBackendUrl(localStorage.getItem('GPTR_API_URL'));

    const urlParams = new URLSearchParams(window.location.search);
    const apiUrlInUrlParams = sanitizeBrowserBackendUrl(urlParams.get('GPTR_API_URL'));
    const apiUrlFromEnv = sanitizeBrowserBackendUrl(process.env.NEXT_PUBLIC_GPTR_API_URL);
    const backendUrlFromEnv = sanitizeBrowserBackendUrl(process.env.NEXT_PUBLIC_BACKEND_URL);
    const reactAppApiUrl = sanitizeBrowserBackendUrl(process.env.REACT_APP_GPTR_API_URL);

    if (apiUrlInLocalStorage) {
      return apiUrlInLocalStorage;
    } else if (apiUrlInUrlParams) {
      return apiUrlInUrlParams;
    } else if (apiUrlFromEnv) {
      return apiUrlFromEnv;
    } else if (backendUrlFromEnv) {
      return backendUrlFromEnv;
    } else if (reactAppApiUrl) {
      return reactAppApiUrl;
    } else if (purpose === 'langgraph-gui') {
      return host.includes('localhost') ? 'http%3A%2F%2F127.0.0.1%3A8123' : `https://${host}`;
    } else {
      return host.includes('localhost') ? 'http://localhost:8002' : `https://${host}`;
    }
  }
  return '';
};
