import { useRef, Dispatch, SetStateAction } from "react";
import { ResearchResults } from "@/components/ResearchResults";
import InputArea from "@/components/ResearchBlocks/elements/InputArea";
import ChatInput from "@/components/ResearchBlocks/elements/ChatInput";
import LoadingDots from "@/components/LoadingDots";
import { ChatBoxSettings, Data } from "@/types/data";

interface ResearchContentProps {
  showResult: boolean;
  orderedData: Data[];
  answer: string;
  allLogs: any[];
  chatBoxSettings: ChatBoxSettings;
  loading: boolean;
  isInChatMode: boolean;
  isStopped: boolean;
  promptValue: string;
  chatPromptValue: string;
  setPromptValue: Dispatch<SetStateAction<string>>;
  setChatPromptValue: Dispatch<SetStateAction<string>>;
  handleDisplayResult: (question: string) => void;
  handleChat: (message: string) => void;
  handleClickSuggestion: (value: string) => void;
  currentResearchId?: string;
  onShareClick?: () => void;
  reset?: () => void;
  isProcessingChat?: boolean;
  bottomRef?: React.RefObject<HTMLDivElement>;
}

export default function ResearchContent({
  showResult,
  orderedData,
  answer,
  allLogs,
  chatBoxSettings,
  loading,
  isInChatMode,
  isStopped,
  promptValue,
  chatPromptValue,
  setPromptValue,
  setChatPromptValue,
  handleDisplayResult,
  handleChat,
  handleClickSuggestion,
  currentResearchId,
  onShareClick,
  reset,
  isProcessingChat = false,
  bottomRef
}: ResearchContentProps) {
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const internalBottomRef = useRef<HTMLDivElement>(null);
  const finalBottomRef = bottomRef || internalBottomRef;

  return (
    <div className="flex h-full w-full grow flex-col justify-between">
      <div className="container w-full space-y-2">
        {onShareClick && currentResearchId && (
          <div className="flex justify-end mb-4">
            <button 
              onClick={onShareClick}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-md flex items-center gap-2 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share
            </button>
          </div>
        )}
        
        <div className="container space-y-2 task-components">
          <ResearchResults
            orderedData={orderedData}
            answer={answer}
            allLogs={allLogs}
            chatBoxSettings={chatBoxSettings}
            handleClickSuggestion={handleClickSuggestion}
            currentResearchId={currentResearchId}
            isProcessingChat={isProcessingChat}
            onShareClick={onShareClick}
          />
        </div>

        <div className="pt-1 sm:pt-2" ref={chatContainerRef}></div>
        {/* Invisible element for scrolling */}
        <div ref={finalBottomRef} />
      </div>
      
      <div id="input-area" className="container px-4 lg:px-0 mb-4">
        {loading || isProcessingChat ? (
          <div className="mt-4 flex justify-center">
            <LoadingDots />
          </div>
        ) : (
          <div>
            {isInChatMode && !isStopped ? (
              <ChatInput
                promptValue={chatPromptValue}
                setPromptValue={setChatPromptValue}
                handleSubmit={handleChat}
                disabled={loading || isProcessingChat}
              />
            ) : (
              showResult && reset ? (
                <InputArea
                  promptValue={promptValue}
                  setPromptValue={setPromptValue}
                  handleSubmit={handleDisplayResult}
                  disabled={loading}
                  reset={reset}
                  isStopped={isStopped}
                />
              ) : null
            )}
          </div>
        )}
      </div>
    </div>
  );
} 