'use client';

import { useEffect, useSyncExternalStore } from 'react';
import { getHost } from '@/helpers/getHost';

export type BackendStatus = 'checking' | 'online' | 'offline';

interface BackendState {
  host: string;
  status: BackendStatus;
  documents: string[];
}

const initial: BackendState = { host: '', status: 'checking', documents: [] };
let state = initial;
let started = false;
const listeners = new Set<() => void>();

const set = (patch: Partial<BackendState>) => {
  state = { ...state, ...patch };
  listeners.forEach((l) => l());
};

async function check(host = state.host) {
  set({ host, status: 'checking' });
  try {
    // A backend busy with a run can stall its event loop for seconds; that is not offline.
    const res = await fetch(`${host.replace(/\/+$/, '')}/files/`, { signal: AbortSignal.timeout(10_000) });
    if (!res.ok) throw new Error(String(res.status));
    const data: unknown = await res.json();
    const files = (data as { files?: unknown }).files;
    set({ status: 'online', documents: Array.isArray(files) ? files.filter((f): f is string => typeof f === 'string') : [] });
  } catch {
    set({ status: 'offline', documents: [] });
  }
}

/** Saves the address the same way the current app reads it, so both UIs follow it. */
function setHost(url: string) {
  const clean = url.trim().replace(/\/+$/, '');
  if (clean) localStorage.setItem('GPTR_API_URL', clean);
  else localStorage.removeItem('GPTR_API_URL');
  void check(clean || getHost());
}

/** Puts a file in the backend's document folder, which `local` and `hybrid` research read. */
async function upload(file: File) {
  const body = new FormData();
  body.append('file', file);
  const res = await fetch(`${state.host.replace(/\/+$/, '')}/upload/`, { method: 'POST', body });
  if (!res.ok) throw new Error(`Could not upload ${file.name}. The backend answered with ${res.status}.`);
}

async function remove(name: string) {
  const res = await fetch(`${state.host.replace(/\/+$/, '')}/files/${encodeURIComponent(name)}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 404) throw new Error(`Could not remove ${name}. The backend answered with ${res.status}.`);
  set({ documents: state.documents.filter((d) => d !== name) });
}

const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

/** Whether the Python backend answers, shared by every component on the page. */
export function useBackend() {
  const snapshot = useSyncExternalStore(subscribe, () => state, () => initial);

  useEffect(() => {
    if (started) return;
    started = true;
    if (new URLSearchParams(window.location.search).get('backend') === 'offline') {
      set({ host: getHost(), status: 'offline' });
      return;
    }
    void check(getHost());
  }, []);

  return { ...snapshot, check: () => check(), setHost, upload, remove };
}
