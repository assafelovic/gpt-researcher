"use client";

import { ReactNode } from "react";
import SlidingBrainTabs from "@/components/brain/SlidingBrainTabs";
import CodebaseExplorer from "@/components/brain/CodebaseExplorer";
import VisionPanel from "@/components/brain/VisionPanel";
import ChangelogTimeline from "@/components/brain/ChangelogTimeline";
import RoadmapPanel from "@/components/brain/RoadmapPanel";
import { BrainTabId } from "@/lib/brainTabs";

type Props = {
  activeTab: BrainTabId;
  onTabChange: (id: BrainTabId) => void;
  onCodebaseAsk: (question: string) => void;
  askChildren: ReactNode;
};

export default function BrainShell({
  activeTab,
  onTabChange,
  onCodebaseAsk,
  askChildren,
}: Props) {
  return (
    <div className="w-full">
      <div className="mb-2 pt-2">
        <SlidingBrainTabs active={activeTab} onChange={onTabChange} />
      </div>
      <div role="tabpanel" className="min-h-[50vh]">
        {activeTab === "ask" && askChildren}
        {activeTab === "codebase" && (
          <CodebaseExplorer onAsk={onCodebaseAsk} />
        )}
        {activeTab === "vision" && <VisionPanel />}
        {activeTab === "changelog" && <ChangelogTimeline />}
        {activeTab === "roadmap" && <RoadmapPanel />}
      </div>
    </div>
  );
}
