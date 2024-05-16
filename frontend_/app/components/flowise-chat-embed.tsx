"use client";

import { FullPageChat } from "flowise-embed-react";

export default function FlowiseChatEmbed() {
  //   const {
  //     messages,
  //     input,
  //     isLoading,
  //     handleSubmit,
  //     handleInputChange,
  //     reload,
  //     stop,
  //   } = useChat({
  //     api: process.env.NEXT_PUBLIC_CHAT_API,
  //     headers: {
  //       "Content-Type": "application/json", // using JSON because of vercel/ai 2.2.26
  //     },
  //     onError: (error) => {
  //       const message = JSON.parse(error.message);
  //       alert(message.detail);
  //     },
  //   });

  const flowise_chatflow: string = "gemini";
  let chatflow_id = "";

  switch (flowise_chatflow) {
    case "azure":
      chatflow_id = "bb4e796a-b929-4c60-b309-65fbc9c840ce";
      break;
    case "claude":
      chatflow_id = "31512f58-644f-40af-b714-b524b10f57ff";
      break;
    case "gemini":
      chatflow_id = "0bc5de51-b65c-45b7-b29b-d1face1178a0";
      // chatflow_id = "645f9712-b18e-4541-9900-97bade1f8378";
      break;
    case "gemini-2":
      chatflow_id = "4c134a75-a911-4d4a-a4e6-6230b03ae0fb";
      break;
    case "openai":
      chatflow_id = "d8acb58e-7497-43c3-af8b-160651a4f7ac";
      break;
    default:
      chatflow_id = "31512f58-644f-40af-b714-b524b10f57ff";
  }

  const chatflowConfig = {
    // topK: 2
  };

  const observersConfig = {
    // (optional) Allows you to execute code in parent based upon signal observations within the chatbot.
    // The userinput field submitted to bot ("" when reset by bot)
    observeUserInput: (userInput: any) => {
      console.log({ userInput });
    },
    // The bot message stack has changed
    observeMessages: (messages: any) => {
      console.log({ messages });
    },
    // The bot loading signal changed
    observeLoading: (loading: any) => {
      console.log({ loading });
    },
  };

  return (
    <FullPageChat
      chatflowid={chatflow_id}
      apiHost="http://localhost:8081"
      chatflowConfig={chatflowConfig}
      isFullPage={true}
      showTitle={true}
      showPoweredBy={false}
      showAvatar={true}
      showAvatarText={true}
      showSendButton={true}
      showTextInput={true}
      showWelcomeMessage={true}
      showErrorMessage={true}
      showFeedback={true}
      observersConfig={observersConfig}
      //   messages={messages}
      //   input={input}
      //   isLoading={isLoading}
      //   handleSubmit={handleSubmit}
      //   handleInputChange={handleInputChange}
      //   reload={reload}
      //   stop={stop}
      //   handleFeedback={handleFeedback}
      //   handleReset={handleReset}
      //   handleReload={handleReload}
      //   handleStop={handleStop}
      theme={{
        chatWindow: {
          showTitle: true, // show/hide the title bar
          title: "Charlotte AI",
          titleAvatarSrc:
            "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/svg/google-messages.svg",
          welcomeMessage: "Hi, I'm Charlotte! How can I help you today?",
          errorMessage:
            "I'm sorry, I'm not able to answer your question. Please try again.",
          backgroundColor: "#222222",
          //   backgroundColor: "#ffffff",
          //   height: "100%",
          //   width: "100%",
          fontSize: 16,
          showPoweredBy: false,
          poweredByTextColor: "#f7f8ff",
          //   poweredByTextColor: "#303235",
          botMessage: {
            backgroundColor: "#303235",
            textColor: "#f7f8ff",
            showAvatar: true,
            avatarSrc:
              "https://raw.githubusercontent.com/zahidkhawaja/langchain-chat-nextjs/main/public/parroticon.png",
          },
          feedback: {
            color: "#ffffff",
            // color: "#303235",
          },
          userMessage: {
            backgroundColor: "#3B81F6",
            textColor: "#ffffff",
            showAvatar: true,
            avatarSrc:
              "https://raw.githubusercontent.com/zahidkhawaja/langchain-chat-nextjs/main/public/usericon.png",
          },
          textInput: {
            placeholder: "Type your question",
            backgroundColor: "#303235",
            // backgroundColor: "#ffffff",
            textColor: "#ffffff",
            // textColor: "#303235",
            sendButtonColor: "#3B81F6",
          },
        },
      }}
    />
  );
}
