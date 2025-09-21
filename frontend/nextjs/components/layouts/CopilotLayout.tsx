import React, { useRef, useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { ChatBoxSettings } from "@/types/data";
import Image from "next/image";

interface CopilotLayoutProps {
  children: React.ReactNode;
  loading: boolean;
  isStopped: boolean;
  showResult: boolean;
  onStop?: () => void;
  onNewResearch?: () => void;
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
  mainContentRef?: React.RefObject<HTMLDivElement>;
  toastOptions?: Record<string, any>;
  toggleSidebar?: () => void;
}

export default function CopilotLayout({
  children,
  loading,
  isStopped,
  showResult,
  onStop,
  onNewResearch,
  chatBoxSettings,
  setChatBoxSettings,
  mainContentRef,
  toastOptions = {},
  toggleSidebar
}: CopilotLayoutProps) {
  const defaultRef = useRef<HTMLDivElement>(null);
  const contentRef = mainContentRef || defaultRef;
  
  return (
    <main className="flex flex-col min-h-screen">
      <Toaster 
        position="bottom-center" 
        toastOptions={toastOptions}
      />
      
      {/* Show Header only when not in research mode */}
      {!showResult && (
        <Header 
          loading={loading}
          isStopped={isStopped}
          showResult={showResult}
          onStop={onStop || (() => {})}
          onNewResearch={onNewResearch}
          isCopilotMode={true}
        />
      )}
      
      <div 
        ref={contentRef}
        className={`flex-1 flex flex-col ${!showResult ? 'pt-[120px]' : ''}`}
      >
        {children}
      </div>
      
      <div className="relative z-10">
        <Footer setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
      </div>
    </main>
  );
} 