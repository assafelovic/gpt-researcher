'use client';

import { usePathname } from 'next/navigation';
import { createContext, useContext } from 'react';
import type { ReportRow } from '@/lib/research/reports';

const Mock = createContext<ReportRow[] | null>(null);

/** Under `/mocks` the screens show sample reports and never start a real run. */
export const MockMode = ({ archive, children }: { archive: ReportRow[]; children: React.ReactNode }) => (
  <Mock.Provider value={archive}>{children}</Mock.Provider>
);

export const useMock = () => useContext(Mock) !== null;

export const useMockArchive = () => useContext(Mock);

/** Where the app's screens live. The top bar sits outside `MockMode`, so this reads the path. */
export function useLinks() {
  const mock = usePathname().startsWith('/mocks');
  return {
    home: mock ? '/mocks/home' : '/',
    archive: mock ? '/mocks/archive' : '/archive',
    report: (id: string) => (mock ? '/mocks/report' : `/research/${id}`),
  };
}
