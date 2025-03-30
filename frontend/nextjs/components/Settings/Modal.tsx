import React, { useState, useEffect } from "react";
import './Settings.css';
import ChatBox from './ChatBox';
import { ChatBoxSettings } from '@/types/data';

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
  
  const [apiVariables, setApiVariables] = useState({
    DOC_PATH: './my-docs',
  });

  useEffect(() => {
    const storedConfig = localStorage.getItem('apiVariables');
    if (storedConfig) {
      setApiVariables(JSON.parse(storedConfig));
    }

    if(showModal) {
      const header = document.querySelector('.settings .App-header');
      if (header) {
        header.classList.remove('App-header');
      }
    }
  }, [showModal]);

  const handleSaveChanges = () => {
    setChatBoxSettings({
      ...chatBoxSettings
    });
    localStorage.setItem('apiVariables', JSON.stringify(apiVariables));
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

  return (
    <div className="settings">
      <button
        className="bg-purple-500 text-white active:bg-purple-600 font-bold text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
        type="button"
        onClick={() => setShowModal(true)}
      >
        Preferences
      </button>
      {showModal ? (
        <>
          <div className="justify-center items-center flex overflow-x-hidden overflow-y-auto fixed inset-0 z-50 outline-none focus:outline-none">
            <div className="relative w-auto my-6 mx-auto max-w-3xl">
              <div className="border-0 rounded-lg shadow-lg relative flex flex-col w-full bg-white outline-none focus:outline-none">
                <div className="relative p-6 flex-auto">
                  {false && (<div className="tabs">
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
                <div className="flex items-center justify-end p-3">
                  <button
                    className="bg-purple-500 text-white active:bg-emerald-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
                    type="button"
                    onClick={handleSaveChanges}
                  >
                    Save & Close
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="opacity-25 fixed inset-0 z-40 bg-black"></div>
        </>
      ) : null}
    </div>
  );
};

export default Modal;