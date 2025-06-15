export const getHost = (): string => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined') {
    // Try to get the host from localStorage if available
    const storedConfig = localStorage.getItem('apiVariables');
    if (storedConfig) {
      try {
        const config = JSON.parse(storedConfig);
        if (config.API_URL) {
          // Extract host from API_URL
          const url = new URL(config.API_URL);
          return url.host;
        }
      } catch (error) {
        console.error('Error parsing stored API config:', error);
      }
    }

    // Fallback to current host if localStorage not available
    return window.location.host;
  }

  // Fallback for non-browser environments
  return 'localhost:8000';
};
