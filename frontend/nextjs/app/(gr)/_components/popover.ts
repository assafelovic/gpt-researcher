'use client';

import { useEffect, useRef, useState } from 'react';

/** Open state for a popover that closes on outside click or Escape and hands focus back to its trigger. */
export function usePopover<T extends HTMLElement>(initiallyOpen = false) {
  const [open, setOpen] = useState(initiallyOpen);
  const root = useRef<T>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      setOpen(false);
      root.current?.querySelector<HTMLElement>('[aria-expanded]')?.focus();
    };
    const keepOnScreen = () => {
      const panel = root.current?.querySelector<HTMLElement>('[data-popover]');
      if (!panel) return;
      panel.style.translate = '';
      const { left, right } = panel.getBoundingClientRect();
      const width = document.documentElement.clientWidth;
      const edge = 12;
      const shift = right > width - edge ? width - edge - right : left < edge ? edge - left : 0;
      if (shift) panel.style.translate = `${Math.round(shift)}px 0`;
    };
    keepOnScreen();
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', keepOnScreen);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', keepOnScreen);
    };
  }, [open]);

  return { open, setOpen, root };
}

const panelSurface = 'gr-in absolute z-30 bg-paper-hi text-left shadow-[0_24px_50px_-28px_rgba(29,25,21,0.55),0_0_0_1px_rgba(29,25,21,0.14)]';

export const popoverPanel = `${panelSurface} top-[calc(100%+10px)]`;
export const popoverPanelAbove = `${panelSurface} bottom-[calc(100%+10px)]`;
