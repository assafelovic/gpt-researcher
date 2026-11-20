'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useBackend } from './backend';
import { useLinks } from './mode';
import { SettingsButton } from './Settings';
import { openSettings } from './preferences';

export const clock = (seconds: number) => {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
};

export const Eye = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <p className={`gr-eye ${className}`}>{children}</p>
);

export const Arrow = ({ className = '' }: { className?: string }) => (
  <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className={className}>
    <path d="M2.5 8h11M9.5 4l4 4-4 4" />
  </svg>
);

const bare = (url: string) => url.replace(/^https?:\/\//, '');

const REPO = 'https://github.com/assafelovic/gpt-researcher';
const STARS_KEY = 'gptr-github-stars';
const STARS_FALLBACK = 30539;
const STARS_TTL = 60 * 60 * 1000;

/** The repo's star count, cached for an hour because GitHub allows 60 anonymous requests an hour. */
function useStars() {
  const [stars, setStars] = useState(STARS_FALLBACK);
  useEffect(() => {
    try {
      const cached = JSON.parse(localStorage.getItem(STARS_KEY) ?? 'null') as { n: number; at: number } | null;
      if (cached?.n) setStars(cached.n);
      if (cached && Date.now() - cached.at < STARS_TTL) return;
    } catch {
      // A corrupt cache entry is refetched below.
    }
    let alive = true;
    fetch('https://api.github.com/repos/assafelovic/gpt-researcher')
      .then((r) => (r.ok ? r.json() : null))
      .then((repo: { stargazers_count?: number } | null) => {
        if (!repo?.stargazers_count) return;
        localStorage.setItem(STARS_KEY, JSON.stringify({ n: repo.stargazers_count, at: Date.now() }));
        if (alive) setStars(repo.stargazers_count);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  return stars;
}

const GitHubIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
  </svg>
);

function GitHubStar() {
  const stars = useStars().toLocaleString('en-US');
  return (
    <a
      href={REPO}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Star GPT Researcher on GitHub, ${stars} stars`}
      className="inline-flex h-[38px] items-center gap-2.5 px-[11px] text-[13.5px] font-medium shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)] transition-shadow hover:shadow-[inset_0_0_0_1px_#1A1612] sm:pl-3 sm:pr-[5px]"
    >
      <GitHubIcon />
      <span className="hidden sm:inline">Star</span>
      <b className="hidden h-7 items-center bg-paper-deep px-2.5 font-code text-[12px] font-medium tabular-nums sm:inline-flex">{stars}</b>
    </a>
  );
}

/** Which Python backend this browser talks to; the address is changed in Settings. */
export function Connection() {
  const backend = useBackend();
  const label = backend.status === 'online' ? bare(backend.host) : backend.status;
  return (
    <button
      type="button"
      aria-haspopup="dialog"
      aria-label={`Backend: ${label}`}
      onClick={() => openSettings('backend')}
      className={`inline-flex h-8 items-center gap-2.5 font-code text-[11px] tracking-[0.06em] transition-colors ${
        backend.status === 'offline' ? 'text-rubric' : 'text-ink-3 hover:text-ink'
      }`}
    >
      <i
        className={`h-2 w-2 ${backend.status === 'online' ? 'bg-ink' : backend.status === 'offline' ? 'bg-rubric' : 'animate-[gr-blink_1s_steps(2,jump-none)_infinite] bg-ink-3'}`}
        aria-hidden="true"
      />
      <span>Backend</span>
      <span className="underline decoration-rule underline-offset-4">{label}</span>
    </button>
  );
}

export function TopBar() {
  const current = usePathname();
  const links = useLinks();
  const navItems = [
    { href: links.home, label: 'New research', short: 'New' },
    { href: links.archive, label: 'Archive', short: 'Archive' },
    { href: 'https://docs.gptr.dev', label: 'Docs', short: 'Docs' },
  ];
  return (
    <header className="sticky top-0 z-40 grid h-16 grid-cols-[1fr_auto] items-center border-b border-rule-soft bg-paper/90 px-5 backdrop-blur md:grid-cols-[1fr_auto_1fr] md:px-8">
      <Link href={links.home} className="inline-flex items-center gap-2.5 whitespace-nowrap text-[16px] font-semibold tracking-[-0.015em]">
        <span className="gr-mark text-[26px]" aria-hidden="true" />
        GPT Researcher
      </Link>
      <nav className="hidden gap-8 text-[14px] font-medium text-ink-2 md:flex" aria-label="Main">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            aria-current={current === item.href ? 'page' : undefined}
            className="transition-colors hover:text-ink aria-[current=page]:text-ink aria-[current=page]:underline aria-[current=page]:decoration-rubric aria-[current=page]:underline-offset-[22px]"
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="flex items-center gap-5 justify-self-end">
        <nav className="flex gap-5 text-[14px] font-medium text-ink-2 md:hidden" aria-label="Main">
          {navItems.slice(0, 2).map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={current === item.href ? 'page' : undefined}
              className="aria-[current=page]:text-ink aria-[current=page]:underline aria-[current=page]:decoration-rubric aria-[current=page]:underline-offset-[6px]"
            >
              {item.short}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-1">
          <SettingsButton />
          <GitHubStar />
        </div>
      </div>
    </header>
  );
}
