'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { DEFAULT_BRIEF, reportLabel, type BriefValue } from '@/lib/research/brief';
import { liveRuns, rememberedRun, saveChat, sendFeedback, startResearch, stopResearch } from '@/lib/research/live';
import { getReport, storedRun, type StoredChatMessage, type StoredReport } from '@/lib/research/reports';
import { reduceRun } from '@/lib/research/run';
import type { ChatMessage } from '../../_components/Chat';
import RunScreen from '../../_components/RunScreen';
import { Eye } from '../../_components/ui';

type Saved = { status: 'loading' } | { status: 'found'; report: StoredReport } | { status: 'missing' } | { status: 'error' };

const day = (when: number) => new Date(when).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

const toStored = (messages: ChatMessage[]): StoredChatMessage[] =>
  messages
    .filter((m) => !m.pending && !m.error)
    .map(({ id, role, content, pinned, seconds, usedWeb }) => ({ role, content, timestamp: id, pinned, seconds, usedWeb }));

function fromStored(messages: StoredChatMessage[] = []): ChatMessage[] {
  const seen = new Set<number>();
  return messages
    .filter((m) => (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
    .map((m, i) => {
      const id = typeof m.timestamp === 'number' && !seen.has(m.timestamp) ? m.timestamp : i + 1;
      seen.add(id);
      return { id, role: m.role, content: m.content, pinned: m.pinned, seconds: m.seconds, usedWeb: m.usedWeb };
    });
}

function Notice({ eyebrow, title, children }: { eyebrow: string; title: string; children?: React.ReactNode }) {
  return (
    <main className="mx-auto w-full max-w-[720px] px-5 pb-40 pt-[12vh] sm:px-8">
      <Eye>{eyebrow}</Eye>
      <h1 className="mt-5 text-balance font-display text-[clamp(1.9rem,3.2vw,2.8rem)] font-semibold leading-[1.08] tracking-[-0.025em]">{title}</h1>
      {children && <div className="mt-6 text-[16px] leading-relaxed text-ink-2">{children}</div>}
    </main>
  );
}

const textLink = 'text-[14px] font-medium underline decoration-rule underline-offset-4 hover:decoration-rubric';

/** A report page: the run streaming in this tab, or a report from the backend's store. */
export default function ResearchScreen({ id }: { id: string }) {
  const router = useRouter();
  const live = useSyncExternalStore(
    useCallback((listener: () => void) => liveRuns.subscribe(id, listener), [id]),
    () => liveRuns.get(id),
    () => undefined,
  );
  const isLive = live !== undefined;
  const [saved, setSaved] = useState<Saved>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [now, setNow] = useState(0);

  useEffect(() => {
    if (isLive) return;
    let current = true;
    setSaved({ status: 'loading' });
    getReport(id).then(
      (report) => current && setSaved(report ? { status: 'found', report } : { status: 'missing' }),
      () => current && setSaved({ status: 'error' }),
    );
    return () => {
      current = false;
    };
  }, [id, isLive, attempt]);

  const startedAt = live && !live.ended ? live.startedAt : undefined;
  useEffect(() => {
    if (startedAt === undefined) return;
    const tick = () => setNow((performance.now() - startedAt) / 1000);
    tick();
    const timer = window.setInterval(tick, 500);
    return () => window.clearInterval(timer);
  }, [startedAt]);

  const run = useMemo(() => {
    if (live) return reduceRun(live.question, live.events, { now, stoppedAt: live.stoppedAt });
    if (saved.status === 'found') return storedRun(saved.report);
  }, [live, now, saved]);

  const restart = (question: string, brief: BriefValue) => router.replace(`/research/${startResearch(question, brief)}`);
  const onChatChange = useCallback((messages: ChatMessage[]) => void saveChat(id, toStored(messages)).catch(() => undefined), [id]);

  if (run && live) {
    return (
      <RunScreen
        key={id}
        run={run}
        label={reportLabel(live.brief.report_type)}
        date={day(Date.now())}
        sharePath={`/research/${id}`}
        chatInitial={fromStored(live.chat)}
        onChatChange={onChatChange}
        onStop={() => stopResearch(id)}
        onRestart={() => restart(live.question, live.brief)}
        onReview={(notes) => sendFeedback(id, notes)}
      />
    );
  }

  if (run && saved.status === 'found') {
    const { report } = saved;
    return (
      <RunScreen
        key={id}
        run={run}
        label={reportLabel(report.brief?.report_type)}
        date={report.timestamp ? day(report.timestamp) : ''}
        sharePath={`/research/${id}`}
        chatInitial={fromStored(report.chatMessages)}
        onChatChange={onChatChange}
        onRestart={() => restart(report.question, { ...DEFAULT_BRIEF, ...report.brief })}
      />
    );
  }

  if (saved.status === 'error') {
    return (
      <Notice eyebrow="Report" title="Could not reach the backend to open this report">
        <p>Check that the backend is running, then try again.</p>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <button type="button" className="gr-btn" onClick={() => setAttempt((n) => n + 1)}>
            Try again
          </button>
          <Link href="/archive" className={textLink}>
            Archive
          </Link>
        </div>
      </Notice>
    );
  }

  if (saved.status === 'missing') {
    const pending = rememberedRun(id);
    if (pending) {
      return (
        <Notice eyebrow="Interrupted" title={pending.question}>
          <p>This research stopped when the page reloaded, before the report was finished. Your question and settings are kept.</p>
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button type="button" className="gr-btn" onClick={() => restart(pending.question, pending.brief)}>
              Start again
            </button>
            <Link href="/" className={textLink}>
              New research
            </Link>
          </div>
        </Notice>
      );
    }
    return (
      <Notice eyebrow="Report" title="This report isn't on the backend">
        <p>It may have been deleted, or saved by a different backend.</p>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <Link href="/archive" className="gr-btn">
            Open the archive
          </Link>
          <Link href="/" className={textLink}>
            New research
          </Link>
        </div>
      </Notice>
    );
  }

  return (
    <div role="status" className="mx-auto max-w-[720px] px-5 pt-[12vh] font-code text-[11.5px] uppercase tracking-[0.14em] text-ink-3 sm:px-8">
      Opening the report
    </div>
  );
}
