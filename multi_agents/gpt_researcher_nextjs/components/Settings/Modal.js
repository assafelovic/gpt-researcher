import React, { useState, useEffect } from "react";
import './App.css';
import ChatBox from './ChatBox';
import axios from 'axios';

export default function Modal({ setChatBoxSettings, chatBoxSettings }) {
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('search');
  const [apiVariables, setApiVariables] = useState({
    ANTHROPIC_API_KEY: '',
    TAVILY_API_KEY: '',
    LANGCHAIN_TRACING_V2: 'true',
    LANGCHAIN_API_KEY: '',
    OPENAI_API_KEY: '',
    DOC_PATH: '',
    RETRIEVER: '',
    GOOGLE_API_KEY: '',
    GOOGLE_CX_KEY: '',
    BING_API_KEY: '',
    SERPAPI_API_KEY: '',
    SERPER_API_KEY: '',
    SEARX_URL: ''
  });

  useEffect(() => {
    const storedConfig = localStorage.getItem('apiVariables');
    if (storedConfig) {
      setApiVariables(JSON.parse(storedConfig));
    } else {
      axios.get('http://localhost:8000/getConfig')
        .then(response => {
          setApiVariables(response.data);
          localStorage.setItem('apiVariables', JSON.stringify(response.data));
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
        localStorage.setItem('apiVariables', JSON.stringify(apiVariables));
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
    localStorage.setItem('apiVariables', JSON.stringify({
      ...apiVariables,
      [name]: value
    }));
  };

  const renderConditionalInputs = () => {
    switch (apiVariables.RETRIEVER) {
      case 'google':
        return (
          <>
            <label>
              GOOGLE_API_KEY:
              <input type="text" name="GOOGLE_API_KEY" value={apiVariables.GOOGLE_API_KEY} onChange={handleInputChange} />
            </label>
            <label>
              GOOGLE_CX_KEY:
              <input type="text" name="GOOGLE_CX_KEY" value={apiVariables.GOOGLE_CX_KEY} onChange={handleInputChange} />
            </label>
          </>
        );
      case 'bing':
        return (
          <label>
            BING_API_KEY:
            <input type="text" name="BING_API_KEY" value={apiVariables.BING_API_KEY} onChange={handleInputChange} />
          </label>
        );
      case 'serpapi':
        return (
          <label>
            SERPAPI_API_KEY:
            <input type="text" name="SERPAPI_API_KEY" value={apiVariables.SERPAPI_API_KEY} onChange={handleInputChange} />
          </label>
        );
      case 'googleSerp':
        return (
          <label>
            SERPER_API_KEY:
            <input type="text" name="SERPER_API_KEY" value={apiVariables.SERPER_API_KEY} onChange={handleInputChange} />
          </label>
        );
      case 'searx':
        return (
          <label>
            SEARX_URL:
            <input type="text" name="SEARX_URL" value={apiVariables.SEARX_URL} onChange={handleInputChange} />
          </label>
        );
      case 'tavily':
        return (
          <label>
            TAVILY_API_KEY:
            <input type="text" name="TAVILY_API_KEY" value={apiVariables.TAVILY_API_KEY} onChange={handleInputChange} />
          </label>
        );
      // Add cases for other retrievers if needed
      default:
        return null;
    }
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
                        ANTHROPIC_API_KEY:
                        <input type="text" name="ANTHROPIC_API_KEY" value={apiVariables.ANTHROPIC_API_KEY} onChange={handleInputChange} />
                      </label>
                      <label>
                        TAVILY_API_KEY:
                        <input type="text" name="TAVILY_API_KEY" value={apiVariables.TAVILY_API_KEY} onChange={handleInputChange} />
                      </label>
                      <label>
                        LANGCHAIN_TRACING_V2:
                        <input type="text" name="LANGCHAIN_TRACING_V2" value={apiVariables.LANGCHAIN_TRACING_V2} onChange={handleInputChange} />
                      </label>
                      <label>
                        LANGCHAIN_API_KEY:
                        <input type="text" name="LANGCHAIN_API_KEY" value={apiVariables.LANGCHAIN_API_KEY} onChange={handleInputChange} />
                      </label>
                      <label>
                        OPENAI_API_KEY:
                        <input type="text" name="OPENAI_API_KEY" value={apiVariables.OPENAI_API_KEY} onChange={handleInputChange} />
                      </label>
                      <label>
                        DOC_PATH:
                        <input type="text" name="DOC_PATH" value={apiVariables.DOC_PATH} onChange={handleInputChange} />
                      </label>
                      <label>
                        RETRIEVER:
                        <select name="RETRIEVER" value={apiVariables.RETRIEVER} onChange={handleInputChange}>
                          <option value="" disabled>Select Retriever</option>
                          <option value="google">Google</option>
                          <option value="searx">Searx</option>
                          <option value="serpapi">SerpApi</option>
                          <option value="googleSerp">GoogleSerp</option>
                          <option value="duckduckgo">DuckDuckGo</option>
                          <option value="bing">Bing</option>
                          <option value="tavily">Tavily</option>
                        </select>
                      </label>
                      {renderConditionalInputs()}
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