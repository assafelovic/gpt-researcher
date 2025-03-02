export const injectFavicons = (basePath = '') => {
    if (typeof document !== 'undefined') {
      const link = document.createElement('link');
      link.rel = 'icon';
      link.href = `${basePath}/favicon.ico`;
      document.head.appendChild(link);
      
      // Add other favicons as needed
    }
  };