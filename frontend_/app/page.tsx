import Header from "@/app/components/header";
// import ChatSection from "./components/chat-section";
import LangChainChatSection from "./components/langchain-chat-section";
import FlowiseChatEmbed from "./components/flowise-chat-embed";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-10 p-24 background-gradient">
      {/* <Header /> */}
      {/* <LangChainChatSection></LangChainChatSection> */}
      <FlowiseChatEmbed></FlowiseChatEmbed>
      {/* <ChatSection /> */}
    </main>
  );
}
