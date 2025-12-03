import { ReactNode, useRef, useCallback, useEffect, Dispatch, SetStateAction } from "react";
import { Toaster } from "react-hot-toast";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { ChatBoxSettings } from "@/types/data";

interface ResearchPageLayoutProps {
  children: ReactNode;
  loading: boolean;
  isStopped: boolean;
  showResult: boolean;
  onStop?: () => void;
  onNewResearch: () => void;
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: Dispatch<SetStateAction<ChatBoxSettings>>;
  mainContentRef?: React.RefObject<HTMLDivElement>;
  showScrollButton?: boolean;
  onScrollToBottom?: () => void;
  toastOptions?: object;
}

export default function ResearchPageLayout({
  children,
  loading,
  isStopped,
  showResult,
  onStop,
  onNewResearch,
  chatBoxSettings,
  setChatBoxSettings,
  mainContentRef,
  showScrollButton = false,
  onScrollToBottom,
  toastOptions = {}
}: ResearchPageLayoutProps) {
  const defaultRef = useRef<HTMLDivElement>(null);
  const contentRef = mainContentRef || defaultRef;

  return (
    <main className="flex min-h-screen flex-col">
      <Toaster 
        position="bottom-center" 
        toastOptions={toastOptions}
      />
      
      <Header 
        loading={loading}
        isStopped={isStopped}
        showResult={showResult}
        onStop={onStop || (() => {})}
        onNewResearch={onNewResearch}
      />
      
      <div 
        ref={contentRef}
        className="min-h-[100vh] pt-[120px]"
      >
        {children}
      </div>
      
      {showScrollButton && showResult && (
        <button
          onClick={onScrollToBottom}
          className="fixed bottom-8 right-8 flex items-center justify-center w-12 h-12 text-white bg-gradient-to-br from-teal-500 to-teal-600 rounded-full hover:from-teal-600 hover:to-teal-700 transform hover:scale-105 transition-all duration-200 shadow-lg z-50 backdrop-blur-sm border border-teal-400/20"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-6 w-6" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M19 14l-7 7m0 0l-7-7m7 7V3" 
            />
          </svg>
        </button>
      )}
      
      <Footer setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
    </main>
  );
} 