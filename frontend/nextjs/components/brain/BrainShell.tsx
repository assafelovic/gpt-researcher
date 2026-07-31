"use client";

import { ReactNode } from "react";
import SlidingBrainTabs from "@/components/brain/SlidingBrainTabs";
import CodebaseExplorer from "@/components/brain/CodebaseExplorer";
import VisionPanel from "@/components/brain/VisionPanel";
import ChangelogTimeline from "@/components/brain/ChangelogTimeline";
import RoadmapPanel from "@/components/brain/RoadmapPanel";
import AudiencePanel from "@/components/brain/AudiencePanel";
import LibraryPanel from "@/components/brain/LibraryPanel";
import StarterPrompts from "@/components/brain/StarterPrompts";
import { BrainTabId } from "@/lib/brainTabs";
import { StarterPrompt } from "@/lib/starterPrompts";

type Props = {
  activeTab: BrainTabId;
  onTabChange: (id: BrainTabId) => void;
  onCodebaseAsk: (question: string) => void;
  onStarterPrompt?: (prompt: StarterPrompt) => void;
  askChildren: ReactNode;
};

export default function BrainShell({
  activeTab,
  onTabChange,
  onCodebaseAsk,
  onStarterPrompt,
  askChildren,
}: Props) {
  const starters = onStarterPrompt ? (
    <StarterPrompts tab={activeTab} onSelect={onStarterPrompt} />
  ) : null;

  return (
    <div className="w-full">
      <div className="mb-2 pt-2">
        <SlidingBrainTabs active={activeTab} onChange={onTabChange} />
      </div>
      <div role="tabpanel" className="min-h-[50vh]">
        {activeTab === "ask" && (
          <>
            {askChildren}
            {starters}
          </>
        )}
        {activeTab === "audience" && (
          <>
            {starters}
            <AudiencePanel />
          </>
        )}
        {activeTab === "codebase" && (
          <>
            {starters}
            <CodebaseExplorer onAsk={onCodebaseAsk} />
          </>
        )}
        {activeTab === "library" && (
          <>
            {starters}
            <LibraryPanel />
          </>
        )}
        {activeTab === "vision" && (
          <>
            {starters}
            <VisionPanel />
          </>
        )}
        {activeTab === "changelog" && (
          <>
            {starters}
            <ChangelogTimeline />
          </>
        )}
        {activeTab === "roadmap" && (
          <>
            {starters}
            <RoadmapPanel />
          </>
        )}
      </div>
    </div>
  );
}
