'use client';

import { useState } from 'react';

export const faviconUrl = (domain: string) => `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;

/** A site's icon on a small paper tile, or its initial when the icon will not load. */
export function Favicon({ domain, size = 'sm', className = '' }: { domain: string; size?: 'sm' | 'md'; className?: string }) {
  const [failed, setFailed] = useState(false);
  const px = size === 'md' ? 16 : 12;
  return (
    <span
      aria-hidden="true"
      className={`gr-fav-tile inline-grid flex-none place-items-center overflow-hidden bg-paper-hi align-middle ${size === 'md' ? 'h-[22px] w-[22px]' : 'h-[18px] w-[18px]'} ${className}`}
    >
      {failed ? (
        <span className="font-code text-[9.5px] font-medium uppercase leading-none text-ink-2">{domain.charAt(0)}</span>
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={faviconUrl(domain)} alt="" width={px} height={px} loading="lazy" decoding="async" onError={() => setFailed(true)} />
      )}
    </span>
  );
}

/** Overlapping icons for a set of sites, most relevant first. */
export function FaviconStack({ domains, max = 4, size = 'sm', label }: { domains: string[]; max?: number; size?: 'sm' | 'md'; label?: string }) {
  const unique = Array.from(new Set(domains));
  const shown = unique.slice(0, max);
  const more = unique.length - shown.length;
  if (!shown.length) return null;
  return (
    <span className="inline-flex flex-none items-center align-middle" role={label ? 'img' : undefined} aria-label={label}>
      <span className="gr-stack inline-flex">
        {shown.map((d) => (
          <Favicon key={d} domain={d} size={size} />
        ))}
      </span>
      {more > 0 && (
        <span className="ml-1.5 font-code text-[10.5px] tabular-nums text-ink-3" aria-hidden="true">
          +{more}
        </span>
      )}
    </span>
  );
}

/** A scraped image that removes itself when it fails or turns out to be an icon or spacer. */
export function Thumb({ src, className = '' }: { src: string; className?: string }) {
  const [hidden, setHidden] = useState(false);
  if (hidden) return null;
  return (
    <span className={`gr-in block overflow-hidden bg-paper-deep ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt=""
        loading="lazy"
        decoding="async"
        referrerPolicy="no-referrer"
        onError={() => setHidden(true)}
        onLoad={(e) => e.currentTarget.naturalWidth < 120 && setHidden(true)}
        className="h-full w-full object-cover mix-blend-multiply"
      />
    </span>
  );
}

export const domainsBySources = (sources: { domain: string; citations: number }[]) =>
  [...sources].sort((a, b) => b.citations - a.citations).map((s) => s.domain);
