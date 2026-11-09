'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ResearchEvent } from '@/lib/research/events';
import { reduceRun, type RunState } from '@/lib/research/run';
import RunScreen, { type Tab } from '../../_components/RunScreen';
import { clock } from '../../_components/ui';
import { sampleChat, scenarios, type ScenarioName } from '../_data/scenarios';

function useReplay(duration: number, at?: number) {
  const [t, setT] = useState(at ?? 0);
  const [playing, setPlaying] = useState(at === undefined);
  const [speed, setSpeed] = useState(4);

  useEffect(() => {
    if (!playing) return;
    const started = performance.now();
    const from = t;
    const id = window.setInterval(() => {
      const next = from + ((performance.now() - started) / 1000) * speed;
      if (next >= duration) {
        setT(duration);
        setPlaying(false);
      } else setT(next);
    }, 100);
    return () => window.clearInterval(id);
    // `t` is only the starting point of this playback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, speed, duration]);

  return { t, setT, playing, setPlaying, speed, setSpeed };
}

function ReplayBar({ replay, duration }: { replay: ReturnType<typeof useReplay>; duration: number }) {
  return (
    <div className="fixed bottom-[72px] left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 bg-ink px-3 py-2 font-code text-[11px] text-paper-hi shadow-lg">
      <button type="button" onClick={() => replay.setPlaying(!replay.playing)} className="w-14 text-left uppercase tracking-[0.12em] text-[#E6DDCA]">
        {replay.playing ? 'Pause' : 'Play'}
      </button>
      <input
        type="range"
        min={0}
        max={duration}
        step={0.5}
        value={replay.t}
        onChange={(e) => replay.setT(Number(e.target.value))}
        aria-label="Replay position"
        className="w-[min(40vw,320px)] accent-[#B8381C]"
      />
      <span className="w-[76px] tabular-nums">
        {clock(replay.t)} / {clock(duration)}
      </span>
      <button type="button" onClick={() => replay.setSpeed(replay.speed === 4 ? 1 : replay.speed === 1 ? 10 : 4)} className="w-8 text-[#E6DDCA]">
        {replay.speed}x
      </button>
    </div>
  );
}

const quoted = (sections: string[]) => sections.map((s) => `'${s.replace(/'/g, "\\'")}'`).join(', ');

/** Replays a recorded run through the real report screen, for design review and tests. */
export default function MockRun({
  scenario = 'nvidia',
  at,
  stopped = false,
  tab,
  withFollowUps = false,
  figure,
  chrome = true,
}: {
  scenario?: ScenarioName;
  at?: number;
  stopped?: boolean;
  tab?: Tab;
  withFollowUps?: boolean;
  figure?: number;
  chrome?: boolean;
}) {
  const base = scenarios[scenario];
  const [extra, setExtra] = useState<ResearchEvent[]>([]);
  const events = useMemo(() => [...base.events, ...extra], [base, extra]);
  const duration = events[events.length - 1].t;
  const replay = useReplay(duration, at === undefined ? undefined : Math.min(at, duration));
  const [stoppedAt, setStoppedAt] = useState(stopped && at !== undefined ? Math.min(at, duration) : undefined);

  const visible = useMemo(() => {
    const i = events.findIndex((e) => e.t > replay.t);
    return i === -1 ? events.length : i;
  }, [events, replay.t]);
  const reduced = useMemo(() => reduceRun(base.query, events.slice(0, visible), { stoppedAt }), [base.query, events, visible, stoppedAt]);
  const run = useMemo<RunState>(
    () => (['done', 'failed', 'stopped'].includes(reduced.status) ? reduced : { ...reduced, elapsed: replay.t }),
    [reduced, replay.t],
  );

  const stop = () => {
    replay.setPlaying(false);
    setStoppedAt(replay.t);
  };

  const restart = () => {
    setStoppedAt(undefined);
    setExtra([]);
    replay.setT(0);
    replay.setPlaying(true);
  };

  const reply = (notes: string | null) => {
    const t = replay.t;
    const sections = run.review?.sections ?? [];
    const next: ResearchEvent[] = notes
      ? [
          { type: 'logs', content: 'planning_research', output: `Revising the outline with your notes: ${notes}`, t: t + 0.5 },
          {
            type: 'human_feedback',
            content: 'request',
            output: `Any feedback on this plan of topics to research? [${quoted([...sections, notes.replace(/[.!]+$/, '')])}]? If not, please reply with 'no'.`,
            t: t + 6,
          },
        ]
      : [
          { type: 'logs', content: 'subqueries', output: 'Researching the planned sections', metadata: sections, t: t + 0.5 },
          ...sections.slice(0, 3).map(
            (s, i): ResearchEvent => ({ type: 'logs', content: 'running_subquery_research', output: `Running research for '${s}'...`, t: t + 1.5 + i }),
          ),
        ];
    setExtra((x) => [...x, ...next]);
    replay.setPlaying(true);
  };

  return (
    <>
      <RunScreen
        run={run}
        label={base.label}
        date="Nov 8, 2026"
        sharePath="/mocks/report"
        chatInitial={withFollowUps ? sampleChat : []}
        onStop={stop}
        onRestart={restart}
        onReview={reply}
        initialTab={tab}
        initialFigure={figure}
      />
      {chrome && at === undefined && <ReplayBar replay={replay} duration={duration} />}
    </>
  );
}
