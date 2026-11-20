import type { Question, RunState, Stage } from '@/lib/research/run';
import { FaviconStack } from './Favicon';
import { clock } from './ui';

export const statusWord: Record<RunState['status'], string> = {
  idle: 'Ready',
  researching: 'Researching',
  review: 'Waiting for you',
  drafting: 'Drafting',
  writing: 'Writing',
  done: 'Done',
  stopped: 'Stopped',
  failed: 'Failed',
};

export const stageTime = (stage: Stage, now: number) => {
  if (stage.startedAt === undefined) return '';
  return clock((stage.endedAt ?? now) - stage.startedAt);
};

export const questionMark: Record<Question['status'], string> = {
  queued: 'bg-rule-soft',
  searching: 'bg-rubric animate-[gr-blink_1.2s_steps(2,jump-none)_infinite]',
  reading: 'bg-rubric',
  done: 'bg-ink',
  empty: 'shadow-[inset_0_0_0_1px_#5F574B]',
  stopped: 'shadow-[inset_0_0_0_1px_#B8381C]',
};

/** One mark per research question, so the search reads at a glance. */
export function QuestionMarks({ questions }: { questions: Question[] }) {
  return (
    <span className="flex gap-[3px]" aria-hidden="true">
      {questions.map((q) => (
        <i key={q.text} className={`h-[6px] w-4 ${questionMark[q.status]}`} />
      ))}
    </span>
  );
}

function Signal({ stage, run }: { stage: Stage; run: RunState }) {
  if (stage.status === 'waiting') return null;
  if (stage.id === 'search' && run.questions.length) return <QuestionMarks questions={run.questions} />;
  if (stage.id === 'read' && run.sources.length) {
    const latest = [...run.sources].reverse().map((s) => s.domain);
    return <FaviconStack domains={latest} max={5} />;
  }
  return null;
}

export function StageList({ run }: { run: RunState }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="gr-meta">{statusWord[run.status]}</p>
        <p className="font-code text-[30px] font-medium tabular-nums tracking-[-0.02em]">{clock(run.elapsed)}</p>
      </div>
      <ol className="mt-5 border-t border-ink">
        {run.stages.map((stage) => (
          <li key={stage.id} className="border-b border-rule py-3.5" data-status={stage.status}>
            <div className="flex items-center gap-3">
              <i className="gr-dot" data-status={stage.status} aria-hidden="true" />
              <span
                className={`flex-1 font-code text-[11.5px] font-medium uppercase tracking-[0.14em] ${stage.status === 'waiting' ? 'text-ink-3' : 'text-ink'}`}
              >
                {stage.label}
              </span>
              <span className="font-code text-[11px] tabular-nums text-ink-3">{stageTime(stage, run.elapsed)}</span>
            </div>
            {stage.detail && stage.status !== 'waiting' && (
              <p className="mt-1.5 pl-[21px] text-[13.5px] leading-snug text-ink-2">{stage.detail}</p>
            )}
            <div className="pl-[21px] empty:hidden [&>*]:mt-2.5">
              <Signal stage={stage} run={run} />
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** One line for narrow screens: the five stages as segments of a bar. */
export function StageStrip({ run }: { run: RunState }) {
  const failed = run.stages.find((s) => s.status === 'failed');
  const active = run.stages.filter((s) => s.status === 'active');
  const detail = [...active].reverse().find((s) => s.detail && s.detail !== statusWord[run.status])?.detail;
  const line = failed
    ? `${statusWord[run.status]} at ${failed.label}`
    : [statusWord[run.status], detail ?? active.at(-1)?.label].filter(Boolean).join(' · ');
  return (
    <span className="flex items-center gap-4">
      <span className="min-w-0 flex-1">
        <span className="flex gap-[3px]" aria-hidden="true">
          {run.stages.map((stage) => (
            <i
              key={stage.id}
              className={`h-[5px] flex-1 ${
                stage.status === 'done'
                  ? 'bg-ink'
                  : stage.status === 'active'
                    ? 'animate-[gr-blink_1.2s_steps(2,jump-none)_infinite] bg-rubric'
                    : stage.status === 'failed'
                      ? 'bg-rubric'
                      : 'bg-rule-soft'
              }`}
            />
          ))}
        </span>
        <span className="mt-2 block truncate font-code text-[10.5px] uppercase tracking-[0.12em] text-ink-2">{line}</span>
      </span>
      <span className="font-code text-[20px] font-medium tabular-nums">{clock(run.elapsed)}</span>
    </span>
  );
}
