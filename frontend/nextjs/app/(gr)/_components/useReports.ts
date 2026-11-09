'use client';

import { useEffect, useMemo, useSyncExternalStore } from 'react';
import { reportsStore, summarize } from '@/lib/research/reports';
import { useMockArchive } from './mode';

/** The archive's rows, newest first: the backend's reports, or the sample ones under `/mocks`. */
export function useReports() {
  const sample = useMockArchive();
  const store = useSyncExternalStore(reportsStore.subscribe, reportsStore.get, reportsStore.get);

  useEffect(() => {
    if (!sample) void reportsStore.refresh();
  }, [sample]);

  const rows = useMemo(
    () => sample ?? store.reports.filter((r) => r.answer?.trim()).map(summarize).sort((a, b) => b.timestamp - a.timestamp),
    [sample, store.reports],
  );
  return { rows, status: sample ? ('ready' as const) : store.status };
}
