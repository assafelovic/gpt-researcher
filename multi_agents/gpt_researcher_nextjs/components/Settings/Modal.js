import React, { useState, useEffect } from "react";
import './App.css';
import ChatBox from './ChatBox';
import axios from 'axios';

export default function Modal({ setChatBoxSettings, chatBoxSettings }) {
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('search');
  const [apiVariables, setApiVariables] = useState({
    OPENAI_API_KEY: '',
    LANGRAPH_API_KEY: '',
    LANGGRAPH_HOST_URL: ''
  });

  useEffect(() => {
    if (showModal) {
      axios.get('http://localhost:8000/getConfig')
        .then(response => {
          setApiVariables(response.data);
        })
        .catch(error => {
          console.error('Error fetching config:', error);
        });
    }
  }, [showModal]);

  const handleSaveChanges = () => {
    setChatBoxSettings(chatBoxSettings);
    axios.post('http://localhost:8000/setConfig', apiVariables)
      .then(response => {
        console.log('Config saved:', response.data);
      })
      .catch(error => {
        console.error('Error saving config:', error);
      });
    setShowModal(false);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setApiVariables(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  return (
    <div className="settings">
      <button
        className="bg-purple-500 text-white active:bg-purple-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
        type="button"
        onClick={() => setShowModal(true)}
      >
        Settings
      </button>
      {showModal ? (
        <>
          <div
            className="justify-center items-center flex overflow-x-hidden overflow-y-auto fixed inset-0 z-50 outline-none focus:outline-none"
          >
            <div className="relative w-auto my-6 mx-auto max-w-3xl">
              <div className="border-0 rounded-lg shadow-lg relative flex flex-col w-full bg-white outline-none focus:outline-none">
                <div className="flex items-start justify-between p-5 border-b border-solid border-blueGray-200 rounded-t">
                  <h3 className="text-3xl font-semibold">
                    Settings
                  </h3>
                  <button
                    className="p-1 ml-auto bg-transparent border-0 text-black opacity-5 float-right text-3xl leading-none font-semibold outline-none focus:outline-none"
                    onClick={() => setShowModal(false)}
                  >
                    <span className="bg-transparent text-black opacity-5 h-6 w-6 text-2xl block outline-none focus:outline-none">
                      ×
                    </span>
                  </button>
                </div>
                <div className="relative p-6 flex-auto">
                  <div className="tabs">
                    <button onClick={() => setActiveTab('search')} className={activeTab === 'search' ? 'active' : ''}>Search Settings</button>
                    <button onClick={() => setActiveTab('api')} className={activeTab === 'api' ? 'active' : ''}>API Variables</button>
                  </div>
                  {activeTab === 'search' && (
                    <div className="App">
                      <header className="App-header">
                        <ChatBox setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
                      </header>
                    </div>
                  )}
                  {activeTab === 'api' && (
                    <div className="api-variables">
                      <label>
                        OPENAI_API_KEY:
                        <input type="text" name="OPENAI_API_KEY" value={apiVariables.OPENAI_API_KEY} onChange={handleInputChange} />
                      </label>
                      <label>
                        LANGRAPH_API_KEY:
                        <input type="text" name="LANGRAPH_API_KEY" value={apiVariables.LANGRAPH_API_KEY} onChange={handleInputChange} />
                      </label>
                      <label>
                        LANGGRAPH_HOST_URL:
                        <input type="text" name="LANGGRAPH_HOST_URL" value={apiVariables.LANGGRAPH_HOST_URL} onChange={handleInputChange} />
                      </label>
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-end p-6 border-t border-solid border-blueGray-200 rounded-b">
                  <button
                    className="bg-emerald-500 text-white active:bg-emerald-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
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
}