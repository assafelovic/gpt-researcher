'use client';

import { useEffect, useRef } from 'react';

const host = (url: string) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
};

export default function Lightbox({ images, index, onIndex, onClose }: { images: string[]; index: number; onIndex: (i: number) => void; onClose: () => void }) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const count = images.length;
  const go = (step: number) => onIndex((index + step + count) % count);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    closeButton.current?.focus();
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
      opener?.focus();
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      else if (e.key === 'ArrowRight') go(1);
      else if (e.key === 'ArrowLeft') go(-1);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  });

  const src = images[index];
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Figure ${index + 1} of ${count}`}
      className="fixed inset-0 z-[80] flex flex-col bg-paper/95 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="flex items-center justify-between gap-4 px-5 py-4 sm:px-8">
        <p className="gr-meta">
          Figure {index + 1} of {count}
          {host(src) && <span className="normal-case tracking-normal"> · {host(src)}</span>}
        </p>
        <button ref={closeButton} type="button" onClick={onClose} className="gr-btn-line">
          Close
        </button>
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center px-5" onClick={(e) => e.target === e.currentTarget && onClose()}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img key={src} src={src} alt={`Figure ${index + 1} from the sources`} className="gr-in max-h-full max-w-[min(1100px,100%)] object-contain shadow-[0_40px_80px_-50px_rgba(29,25,21,0.6)]" />
      </div>
      <div className="flex items-center justify-between gap-4 px-5 py-4 sm:px-8">
        <a href={src} target="_blank" rel="noopener noreferrer" className="text-[13.5px] font-medium underline decoration-rule underline-offset-4 hover:decoration-rubric">
          Open original
        </a>
        {count > 1 && (
          <div className="flex gap-2">
            <button type="button" onClick={() => go(-1)} className="gr-btn-line" aria-label="Previous figure">
              Previous
            </button>
            <button type="button" onClick={() => go(1)} className="gr-btn-line" aria-label="Next figure">
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
