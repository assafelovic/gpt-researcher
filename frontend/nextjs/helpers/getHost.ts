interface GetHostParams {
  purpose?: string;
}

export interface HostResult {
  isSecure: boolean;
  cleanHost: string;
}

export const getHost = ({ purpose }: GetHostParams = {}): HostResult => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    const apiUrlInLocalStorage = localStorage.getItem("GPTR_API_URL");

    const urlParams = new URLSearchParams(window.location.search);
    const apiUrlInUrlParams = urlParams.get("GPTR_API_URL");

    // Debug logging
    console.log('🔍 getHost Debug Info:');
    console.log('  - window.location.host:', host);
    console.log('  - localStorage GPTR_API_URL:', apiUrlInLocalStorage);
    console.log('  - URL param GPTR_API_URL:', apiUrlInUrlParams);
    console.log('  - process.env.NEXT_PUBLIC_GPTR_API_URL:', process.env.NEXT_PUBLIC_GPTR_API_URL);
    console.log('  - process.env.REACT_APP_GPTR_API_URL:', process.env.REACT_APP_GPTR_API_URL);
    console.log('  - purpose:', purpose);
    let selectedUrl: string;

    // Check environment variables first (higher priority)
    if (purpose === 'langgraph-gui') {
        selectedUrl = host.includes('localhost') ? 'http://127.0.0.1:8123' : `https://${host}`;
    } else if (process.env.NEXT_PUBLIC_GPTR_API_URL) {
        selectedUrl = process.env.NEXT_PUBLIC_GPTR_API_URL;
    } else if (process.env.REACT_APP_GPTR_API_URL) {
      selectedUrl = process.env.REACT_APP_GPTR_API_URL;
    } else if (apiUrlInLocalStorage) {
      selectedUrl = apiUrlInLocalStorage;
    } else if (apiUrlInUrlParams) {
      selectedUrl = apiUrlInUrlParams;
    } else {
      selectedUrl = host.includes('localhost') ? 'http://localhost:8000' : `https://${host}`;
    }

    // Parse the selected URL to extract protocol and clean host
    const isSecure = selectedUrl.includes('https');
    const cleanHost = selectedUrl
      .replace('http://', '')
      .replace('https://', '')
      .replace('wss://', '')
      .replace('ws://', '');

    return { isSecure, cleanHost };
  }
  console.log('❌ Window not available, returning empty string');

  return { isSecure: false, cleanHost: '' };
};
