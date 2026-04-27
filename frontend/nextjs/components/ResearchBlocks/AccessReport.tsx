import React, { useMemo, useState } from "react";
import {
  buildReportArtifactLink,
  reportArtifactUnavailableMessage,
  type ReportArtifactKind,
  type ReportArtifactLink,
} from "@/utils/reportArtifacts";

interface AccessReportProps {
  accessData: {
    md?: string;
    pdf?: string;
    docx?: string;
    json?: string;
    research_id?: string;
    run_id?: string;
  };
  chatBoxSettings: {
    report_type?: string;
  };
  report: string;
  researchId?: string;
  hasInlineReport?: boolean;
  onShareClick?: () => void;
}

type ArtifactAction = {
  kind: ReportArtifactKind;
  label: string;
  tone: string;
  icon: React.ReactNode;
  link: ReportArtifactLink;
};

const buttonBaseClass =
  "inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-60";

const AccessReport: React.FC<AccessReportProps> = ({
  accessData,
  chatBoxSettings,
  report,
  researchId,
  hasInlineReport = false,
  onShareClick,
}) => {
  const [artifactError, setArtifactError] = useState<string | null>(null);
  const [failedAction, setFailedAction] = useState<ArtifactAction | null>(null);
  const [loadingArtifactKind, setLoadingArtifactKind] =
    useState<ReportArtifactKind | null>(null);
  const effectiveResearchId =
    researchId || accessData?.research_id || accessData?.run_id || null;

  const artifactActions = useMemo<ArtifactAction[]>(() => {
    const actions: ArtifactAction[] = [];

    const addAction = (
      kind: ReportArtifactKind,
      label: string,
      tone: string,
      icon: React.ReactNode,
    ) => {
      const link = buildReportArtifactLink({
        kind,
        path: accessData?.[kind],
        researchId: effectiveResearchId,
      });
      if (
        link.ok ||
        accessData?.[kind] ||
        (kind === "docx" && effectiveResearchId)
      ) {
        actions.push({ kind, label, tone, icon, link });
      }
    };

    addAction(
      "md",
      "Open Markdown",
      "border-teal-400/30 bg-teal-500/12 text-teal-100 hover:bg-teal-500/20 focus:ring-teal-400/50",
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M7 8h10M7 12h10M7 16h6M5 3h10l4 4v14H5z"
      />,
    );
    addAction(
      "pdf",
      "View PDF",
      "border-cyan-400/30 bg-cyan-500/12 text-cyan-100 hover:bg-cyan-500/20 focus:ring-cyan-400/50",
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />,
    );
    addAction(
      "docx",
      "Download DocX",
      "border-blue-400/30 bg-blue-500/14 text-blue-100 hover:bg-blue-500/24 focus:ring-blue-400/50",
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
      />,
    );

    if (chatBoxSettings?.report_type === "research_report") {
      addAction(
        "json",
        "Download Logs",
        "border-slate-400/30 bg-white/8 text-slate-100 hover:bg-white/12 focus:ring-slate-400/50",
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
        />,
      );
    }

    return actions;
  }, [accessData, chatBoxSettings?.report_type, effectiveResearchId]);

  const openArtifact = async (action: ArtifactAction) => {
    if (!action.link.ok) {
      setArtifactError(action.link.reason);
      setFailedAction(action);
      return;
    }

    setArtifactError(null);
    setFailedAction(null);
    setLoadingArtifactKind(action.kind);

    try {
      const response = await fetch(action.link.href, {
        method: "HEAD",
        cache: "no-store",
      });

      if (!response.ok) {
        setArtifactError(reportArtifactUnavailableMessage(action.kind));
        setFailedAction(action);
        return;
      }

      window.open(action.link.href, "_blank", "noopener,noreferrer");
    } catch {
      setArtifactError(reportArtifactUnavailableMessage(action.kind));
      setFailedAction(action);
    } finally {
      setLoadingArtifactKind(null);
    }
  };

  // Safety check for accessData
  if (!accessData || typeof accessData !== "object") {
    return null;
  }

  const markdownAction = artifactActions.find(
    (action) => action.kind === "md" && action.link.ok,
  );

  return (
    <div className="bg-slate-950/72 container my-4 rounded-lg border border-solid border-teal-400/20 p-4 shadow-lg backdrop-blur-md sm:p-5">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-200">
              Research complete
            </p>
            <h3 className="mt-1 text-lg font-semibold text-white">
              Report artifacts are ready
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              {hasInlineReport || report
                ? "The final report streamed into the page. These files are durable export copies from the same run."
                : "The run completed with durable file metadata but did not stream an inline report. Open the Markdown report first, then use DocX or PDF if available."}
            </p>
          </div>
          {effectiveResearchId ? (
            <code className="rounded-md border border-white/10 bg-black/30 px-2 py-1 text-xs text-slate-300">
              {effectiveResearchId}
            </code>
          ) : null}
        </div>

        {artifactError ? (
          <div className="flex flex-col gap-3 rounded-md border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-sm text-amber-100 sm:flex-row sm:items-center sm:justify-between">
            <span>{artifactError}</span>
            <span className="flex flex-wrap gap-2">
              {failedAction ? (
                <button
                  type="button"
                  onClick={() => void openArtifact(failedAction)}
                  className="rounded-md border border-amber-200/30 bg-amber-200/10 px-2.5 py-1 text-xs font-semibold text-amber-50 transition-colors hover:bg-amber-200/20"
                >
                  Retry
                </button>
              ) : null}
              {markdownAction && failedAction?.kind !== "md" ? (
                <button
                  type="button"
                  onClick={() => void openArtifact(markdownAction)}
                  className="rounded-md border border-teal-200/30 bg-teal-200/10 px-2.5 py-1 text-xs font-semibold text-teal-50 transition-colors hover:bg-teal-200/20"
                >
                  Open Markdown
                </button>
              ) : null}
            </span>
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {artifactActions.map((action) => (
            <button
              key={action.kind}
              type="button"
              onClick={() => void openArtifact(action)}
              disabled={loadingArtifactKind === action.kind}
              className={`${buttonBaseClass} ${action.tone} border`}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {action.icon}
              </svg>
              {loadingArtifactKind === action.kind
                ? "Opening..."
                : action.label}
            </button>
          ))}

          {onShareClick && (
            <button
              onClick={onShareClick}
              className={`${buttonBaseClass} bg-purple-500/12 border border-purple-400/30 text-purple-100 hover:bg-purple-500/20 focus:ring-purple-400/50`}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
              Share Report
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AccessReport;
