'use client';

import { useEffect, useRef, useState } from 'react';
import type { RunState } from '@/lib/research/run';
import { useCitedHtml } from './Sheet';
import { copyText } from './clipboard';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  pending?: boolean;
  error?: boolean;
  seconds?: number;
  usedWeb?: boolean;
  pinned?: boolean;
}

/** Talks to the backend's `/api/chat`, which answers from the report and can search the web. */
export function useChat(report: string, initial: ChatMessage[] = []) {
  const [messages, setMessages] = useState<ChatMessage[]>(initial);
  const busy = messages.some((m) => m.pending);

  const ask = async (question: string, history = messages) => {
    const q = question.trim();
    if (!q || busy) return;
    const id = Date.now();
    const settled = history.filter((m) => !m.pending && !m.error);
    setMessages([...history, { id, role: 'user', content: q }, { id: id + 1, role: 'assistant', content: '', pending: true }]);
    const started = performance.now();

    let patch: Partial<ChatMessage>;
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report, messages: [...settled, { role: 'user', content: q }].map(({ role, content }) => ({ role, content })) }),
      });
      const data = (await res.json()) as { response?: { content?: string; metadata?: { tool_calls?: unknown[] } | null }; error?: string };
      const content = data.response?.content;
      if (!res.ok || !content?.trim()) throw new Error(data.error ?? `The backend answered with ${res.status}.`);
      patch = { content, usedWeb: Boolean(data.response?.metadata?.tool_calls?.length) };
    } catch (e) {
      patch = { content: e instanceof Error ? e.message : String(e), error: true };
    }
    const seconds = (performance.now() - started) / 1000;
    setMessages((ms) => ms.map((m) => (m.id === id + 1 ? { ...m, ...patch, pending: false, seconds } : m)));
  };

  const retry = (answerId: number) => {
    const i = messages.findIndex((m) => m.id === answerId);
    const question = messages[i - 1];
    if (question?.role === 'user') void ask(question.content, messages.slice(0, i - 1));
  };

  const togglePin = (answerId: number) => setMessages((ms) => ms.map((m) => (m.id === answerId ? { ...m, pinned: !m.pinned } : m)));

  return { messages, busy, ask, retry, togglePin };
}

export type Chat = ReturnType<typeof useChat>;

const SUGGESTED = ['What could stop the rally?', 'How much of the revenue comes from data centers?', 'What would change this conclusion?'];

function Thinking() {
  const [s, setS] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setS((v) => v + 1), 1000);
    return () => window.clearInterval(id);
  }, []);
  return (
    <p className="font-code text-[11px] uppercase tracking-[0.12em] text-ink-3">
      Reading the report{s > 2 ? ` · ${s}s` : ''}
      <span className="gr-caret" aria-hidden="true" />
    </p>
  );
}

function Answer({ message, run, chat }: { message: ChatMessage; run: RunState; chat: Chat }) {
  const html = useCitedHtml(message.pending || message.error ? '' : message.content, run.sources);
  const [copied, setCopied] = useState(false);

  if (message.pending) return <Thinking />;
  if (message.error)
    return (
      <div role="alert">
        <p className="text-[14px] leading-snug text-rubric">Could not get an answer. {message.content}</p>
        <button type="button" onClick={() => chat.retry(message.id)} className="mt-2 text-[13px] font-medium underline decoration-rule underline-offset-4 hover:decoration-rubric">
          Try again
        </button>
      </div>
    );

  return (
    <div>
      <div className="gr-prose gr-prose-sm" dangerouslySetInnerHTML={{ __html: html }} />
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 font-code text-[10.5px] uppercase tracking-[0.1em] text-ink-3">
        <span>
          {message.seconds !== undefined && `${Math.max(1, Math.round(message.seconds))}s`}
          {message.usedWeb && ' · searched the web'}
        </span>
        <button
          type="button"
          aria-pressed={message.pinned}
          onClick={() => chat.togglePin(message.id)}
          className={`transition-colors hover:text-ink ${message.pinned ? 'text-rubric' : ''}`}
        >
          {message.pinned ? 'In the report' : 'Add to report'}
        </button>
        <button
          type="button"
          onClick={async () => {
            setCopied(await copyText(message.content));
            window.setTimeout(() => setCopied(false), 1600);
          }}
          className="transition-colors hover:text-ink"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </div>
  );
}

export function ChatThread({ run, chat }: { run: RunState; chat: Chat }) {
  const end = useRef<HTMLDivElement>(null);
  const mounted = useRef(false);
  const ready = run.status === 'done';

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;
      return;
    }
    const box = end.current?.closest<HTMLElement>('[data-scroll-box]');
    if (box) box.scrollTop = box.scrollHeight;
  }, [chat.messages.length, chat.busy]);

  if (!ready)
    return (
      <p className="py-4 text-[13.5px] leading-snug text-ink-3">
        Chat opens when the report is written. Ask about anything in it, and answers cite the same sources.
      </p>
    );

  return (
    <div className="py-4" aria-live="polite">
      {chat.messages.length === 0 ? (
        <>
          <p className="text-[13.5px] leading-snug text-ink-2">Ask about this report. Answers cite its sources, and you can add the good ones to the report.</p>
          <ul className="mt-4 border-t border-rule-soft">
            {SUGGESTED.map((q) => (
              <li key={q} className="border-b border-rule-soft">
                <button type="button" onClick={() => void chat.ask(q)} className="w-full py-2.5 text-left font-display text-[15px] leading-snug transition-colors hover:text-rubric">
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <ol className="space-y-6">
          {chat.messages.map((m) =>
            m.role === 'user' ? (
              <li key={m.id} className="gr-in">
                <p className="font-display text-[16px] font-semibold leading-snug">
                  <span className="mr-1.5 font-code text-[11px] font-medium text-rubric">Q</span>
                  {m.content}
                </p>
              </li>
            ) : (
              <li key={m.id} className="gr-in">
                <Answer message={m} run={run} chat={chat} />
              </li>
            ),
          )}
        </ol>
      )}
      <div ref={end} />
    </div>
  );
}

export function ChatComposer({ run, chat }: { run: RunState; chat: Chat }) {
  const [draft, setDraft] = useState('');
  const ready = run.status === 'done';
  const send = () => {
    if (!draft.trim() || chat.busy) return;
    void chat.ask(draft);
    setDraft('');
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        send();
      }}
      className="border-t border-ink pt-3"
    >
      <label className="block">
        <span className="sr-only">Ask about this report</span>
        <textarea
          rows={2}
          value={draft}
          disabled={!ready}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder={ready ? 'Ask about this report' : 'Available when the report is done'}
          className="gr-input w-full resize-none bg-paper-hi px-3 py-2.5 font-display text-[15px] leading-snug outline-none shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)] focus:shadow-[inset_0_0_0_1px_#1A1612] disabled:opacity-50"
        />
      </label>
      <div className="mt-2 flex items-center justify-between">
        <span className="font-code text-[10.5px] text-ink-3">Enter to send</span>
        <button type="submit" className="gr-btn h-8 px-3.5 text-[13px]" disabled={!ready || !draft.trim() || chat.busy}>
          Ask
        </button>
      </div>
    </form>
  );
}
