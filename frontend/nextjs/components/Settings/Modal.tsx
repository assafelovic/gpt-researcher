import React, { useState, useEffect } from "react";
import './Settings.css';
import ChatBox from './ChatBox';
import { ChatBoxSettings } from '@/types/data';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from "framer-motion";

interface ChatBoxProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

interface Domain {
  value: string;
}

const Modal: React.FC<ChatBoxProps> = ({ chatBoxSettings, setChatBoxSettings }) => {
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('report_settings');
  const [mounted, setMounted] = useState(false);
  
  const [apiVariables, setApiVariables] = useState({
    DOC_PATH: './my-docs',
  });

  // Mount the component
  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  useEffect(() => {
    const storedConfig = localStorage.getItem('apiVariables');
    if (storedConfig) {
      setApiVariables(JSON.parse(storedConfig));
    }

    // Handle body scroll when modal is shown/hidden
    if (showModal) {
      document.body.style.overflow = 'hidden';
      const header = document.querySelector('.settings .App-header');
      if (header) {
        header.classList.remove('App-header');
      }
    } else {
      document.body.style.overflow = '';
    }
    
    // Cleanup function
    return () => {
      document.body.style.overflow = '';
    };
  }, [showModal]);

  const handleSaveChanges = () => {
    setChatBoxSettings({
      ...chatBoxSettings
    });
    // Save both apiVariables AND chatBoxSettings to localStorage
    localStorage.setItem('apiVariables', JSON.stringify(apiVariables));
    localStorage.setItem('chatBoxSettings', JSON.stringify(chatBoxSettings));
    setShowModal(false);
  };

  const handleInputChange = (e: { target: { name: any; value: any; }; }) => {
    const { name, value } = e.target;
    setApiVariables(prevState => ({
      ...prevState,
      [name]: value
    }));
    localStorage.setItem('apiVariables', JSON.stringify({
      ...apiVariables,
      [name]: value
    }));
  };

  // Animation variants
  const fadeIn = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.3 } }
  };

  const slideUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } }
  };

  // Create modal content
  const modalContent = showModal && (
    <AnimatePresence>
      <motion.div 
        key="modal-overlay"
        className="fixed inset-0 z-[1000] flex items-center justify-center overflow-auto" 
        initial="hidden"
        animate="visible"
        exit="hidden"
        variants={fadeIn}
        style={{ backdropFilter: 'blur(5px)' }}
        onClick={(e) => {
          // Close when clicking the backdrop, not the modal content
          if (e.target === e.currentTarget) setShowModal(false);
        }}
      >
        <motion.div 
          className="relative w-auto max-w-3xl z-[1001] mx-6 my-8 md:mx-auto"
          variants={slideUp}
        >
          <div className="relative">
            {/* Subtle border with hint of glow */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-teal-500/20 via-cyan-500/15 to-blue-500/20 rounded-xl blur-sm opacity-50 shadow-sm"></div>
            
            {/* Modal content */}
            <div className="relative flex flex-col rounded-lg overflow-hidden bg-gray-900 border border-gray-800/60 shadow-md hover:shadow-teal-400/10 transition-shadow duration-300">
              {/* Header with subtler accent */}
              <div className="bg-gray-900 p-5 border-b border-gray-800">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-white">
                    <span className="mr-2">⚙️</span>
                    <span className="text-teal-400">Preferences</span>
                  </h3>
                  <button
                    className="p-1 ml-auto text-gray-400 hover:text-white transition-colors duration-200"
                    onClick={() => setShowModal(false)}
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
              </div>
              
              {/* Body with content */}
              <div className="relative p-6 flex-auto bg-gray-900/95 modal-content">
                {false && (<div className="tabs mb-4">
                  <button onClick={() => setActiveTab('report_settings')} className={`tab-button ${activeTab === 'report_settings' ? 'active' : ''}`}>Report Settings</button>
                </div>)}

                {activeTab === 'report_settings' && (
                  <div className="App">
                    <header className="App-header">
                      <ChatBox setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
                    </header>
                  </div>
                )}
              </div>
              
              {/* Footer with actions */}
              <div className="flex items-center justify-end p-4 border-t border-gray-800 bg-gray-900/80">
                <button
                  className="mr-3 px-4 py-2 text-sm font-medium text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-md transition-colors duration-200"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button
                  className="px-6 py-2.5 text-sm font-medium rounded-md text-white bg-teal-600 hover:bg-gradient-to-br hover:from-teal-500/95 hover:via-cyan-500/90 hover:to-teal-600/95 shadow-sm hover:shadow-teal-400/20 transition-all duration-300 focus:outline-none focus:ring-1 focus:ring-teal-500 focus:ring-offset-1 focus:ring-offset-gray-900"
                  onClick={handleSaveChanges}
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
      <motion.div 
        key="modal-background"
        className="fixed inset-0 z-[999] bg-black"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.6 }}
        exit={{ opacity: 0 }}
      ></motion.div>
    </AnimatePresence>
  );

  return (
    <div className="settings">
      <button
        className="bg-gray-900 text-white px-6 py-3 rounded-lg shadow-sm hover:shadow-teal-400/10 transition-all duration-300 border border-gray-800 hover:border-teal-500/30"
        type="button"
        onClick={() => setShowModal(true)}
      >
        <span className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Preferences
        </span>
      </button>
      {mounted && showModal && createPortal(modalContent, document.body)}
    </div>
  );
};

export default Modal;