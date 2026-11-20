'use client';

import { useSyncExternalStore } from 'react';
import { DEFAULT_BRIEF, parseBrief, type BriefValue } from '@/lib/research/brief';

export type SettingsTab = 'research' | 'mcp' | 'documents' | 'backend';

const BRIEF_KEY = 'gptr-brief';

let brief = DEFAULT_BRIEF;
let loaded = false;
let tab: SettingsTab | null = null;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

/** The mocks never read or write the settings saved in this browser. */
const persists = () => !window.location.pathname.startsWith('/mocks');

function load() {
  if (loaded) return;
  loaded = true;
  if (!persists()) return;
  try {
    const saved = localStorage.getItem(BRIEF_KEY);
    if (saved) brief = parseBrief(JSON.parse(saved));
  } catch {
    // A corrupt entry falls back to the defaults and is overwritten on the next change.
  }
}

export function setBrief(next: BriefValue) {
  load();
  brief = next;
  if (persists()) {
    try {
      localStorage.setItem(BRIEF_KEY, JSON.stringify(next));
    } catch {
      // Private mode or a full quota: the brief still applies for this visit.
    }
  }
  emit();
}

/** The brief for the next research, shared by the home screen and Settings. */
export function useBrief() {
  const value = useSyncExternalStore(
    subscribe,
    () => {
      load();
      return brief;
    },
    () => DEFAULT_BRIEF,
  );
  return [value, setBrief] as const;
}

export function openSettings(next: SettingsTab = 'research') {
  tab = next;
  emit();
}

export function closeSettings() {
  tab = null;
  emit();
}

export const useSettingsTab = () =>
  useSyncExternalStore(
    subscribe,
    () => tab,
    () => null,
  );
