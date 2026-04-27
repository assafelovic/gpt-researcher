import Image from "next/image";
import LogMessage from "./elements/LogMessage";
import { useEffect, useRef, useState } from "react";

interface Log {
  header: string;
  text: string;
  metadata: any;
  key: string;
}

interface OrderedLogsProps {
  logs: Log[];
  collapsedByDefault?: boolean;
}

const LogsSection = ({
  logs,
  collapsedByDefault = false,
}: OrderedLogsProps) => {
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(!collapsedByDefault);

  useEffect(() => {
    setExpanded(!collapsedByDefault);
  }, [collapsedByDefault]);

  useEffect(() => {
    // Scroll to bottom whenever logs change
    if (expanded && logsContainerRef.current) {
      logsContainerRef.current.scrollTop =
        logsContainerRef.current.scrollHeight;
    }
  }, [logs, expanded]); // Dependency on logs array ensures this runs when new logs are added

  if (logs.length === 0) return null;

  const latestLog = logs[logs.length - 1];

  return (
    <div className="bg-black/24 container mt-4 h-auto w-full shrink-0 rounded-lg border border-solid border-gray-700/35 p-4 shadow-lg backdrop-blur-md">
      <div className="flex flex-col gap-3 pb-0 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <img src="/img/chat-check.svg" alt="logs" width={20} height={20} />
          <div>
            <h3 className="text-sm font-bold uppercase leading-[152.5%] tracking-[0.08em] text-white">
              Research activity
            </h3>
            {!expanded && latestLog ? (
              <p className="mt-1 max-w-[720px] truncate text-xs leading-5 text-slate-400">
                Latest: {latestLog.text || latestLog.header}
              </p>
            ) : null}
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="inline-flex items-center justify-center rounded-md border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-semibold text-slate-200 transition-colors hover:bg-white/[0.08]"
        >
          {expanded ? "Collapse logs" : `Show ${logs.length} events`}
        </button>
      </div>
      {expanded ? (
        <div
          ref={logsContainerRef}
          className="scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-300/10 mt-3 max-h-[420px] min-h-[180px] overflow-y-auto"
        >
          <LogMessage logs={logs} />
        </div>
      ) : null}
    </div>
  );
};

export default LogsSection;
