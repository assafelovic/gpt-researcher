'use client';

import { usePathname, useSearchParams } from 'next/navigation';

const screens = [
  { href: '/mocks/home', label: 'Home' },
  { href: '/mocks/home?open=report_type', label: 'Brief' },
  { href: '/mocks/home?open=domains', label: 'Sites' },
  { href: '/mocks/home?settings=mcp', label: 'Settings' },
  { href: '/mocks/home?backend=offline', label: 'Offline' },
  { href: '/mocks/run?at=14', label: 'Researching' },
  { href: '/mocks/review', label: 'Plan review' },
  { href: '/mocks/run?at=36', label: 'Drafting' },
  { href: '/mocks/run?at=74', label: 'Writing' },
  { href: '/mocks/run?at=14&stopped=1', label: 'Stopped' },
  { href: '/mocks/report', label: 'Report' },
  { href: '/mocks/report?tab=chat', label: 'Chat' },
  { href: '/mocks/report?followups=1', label: 'Chat answered' },
  { href: '/mocks/report?figure=0', label: 'Figure' },
  { href: '/mocks/failed', label: 'Failed' },
  { href: '/mocks/archive', label: 'Archive' },
  { href: '/mocks/run', label: 'Replay' },
];

export default function MockBar() {
  const pathname = usePathname();
  const params = useSearchParams();
  if (params.get('chrome') === '0') return null;
  const here = `${pathname}${params.toString() ? `?${params}` : ''}`;

  return (
    <nav
      aria-label="Mock screens"
      className="gr-scroll fixed bottom-4 left-1/2 z-50 flex max-w-[calc(100vw-24px)] -translate-x-1/2 gap-1 overflow-x-auto rounded-full bg-ink/90 p-1 font-body text-[12.5px] shadow-lg backdrop-blur"
    >
      {screens.map((s) => (
        <a
          key={s.href}
          href={s.href}
          aria-current={here === s.href ? 'page' : undefined}
          className="whitespace-nowrap rounded-full px-3 py-1.5 text-[#CFC2A6] transition-colors hover:text-paper-hi aria-[current=page]:bg-paper-hi aria-[current=page]:text-ink"
        >
          {s.label}
        </a>
      ))}
    </nav>
  );
}
