import { useState, useEffect, useCallback, RefObject } from 'react';

export function useScrollHandler(
  mainContentRef: RefObject<HTMLDivElement>
) {
  const [showScrollButton, setShowScrollButton] = useState(false);

  const handleScroll = useCallback(() => {
    // Calculate if we're near bottom (within 100px)
    const scrollPosition = window.scrollY + window.innerHeight;
    const nearBottom = scrollPosition >= document.documentElement.scrollHeight - 100;
    
    // Show button if we're not near bottom and page is scrollable
    const isPageScrollable = document.documentElement.scrollHeight > window.innerHeight;
    setShowScrollButton(isPageScrollable && !nearBottom);
  }, []);

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
  };

  // Add ResizeObserver to watch for content changes
  useEffect(() => {
    const mainContentElement = mainContentRef.current;
    const resizeObserver = new ResizeObserver(() => {
      handleScroll();
    });

    if (mainContentElement) {
      resizeObserver.observe(mainContentElement);
    }

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleScroll);
    
    return () => {
      if (mainContentElement) {
        resizeObserver.unobserve(mainContentElement);
      }
      resizeObserver.disconnect();
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, [handleScroll, mainContentRef]);

  return {
    showScrollButton,
    scrollToBottom
  };
} 