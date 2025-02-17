import React, { useState, useEffect } from "react";
import './App.css';
import ChatBox from './ChatBox';
import { CloseIcon } from '@chakra-ui/icons'

interface ChatBoxSettings {
  report_source: string;
  report_type: string;
  tone: string;
}

interface ChatBoxProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

interface Domain {
  value: string;
}

export default function Modal({ setChatBoxSettings, chatBoxSettings }: ChatBoxProps) {
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('search');
  const [domains, setDomains] = useState<Domain[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('domainFilters');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const [newDomain, setNewDomain] = useState('');
  
  const [apiVariables, setApiVariables] = useState({
    DOC_PATH: './my-docs',
  });

  useEffect(() => {
    const storedConfig = localStorage.getItem('apiVariables');
    if (storedConfig) {
      setApiVariables(JSON.parse(storedConfig));
    }
  }, [showModal]);

  const handleSaveChanges = () => {
    setChatBoxSettings(chatBoxSettings);
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

  useEffect(() => {
    localStorage.setItem('domainFilters', JSON.stringify(domains));
  }, [domains]);

  const handleAddDomain = (e: React.FormEvent) => {
    e.preventDefault();
    if (newDomain.trim()) {
      setDomains([...domains, { value: newDomain.trim() }]);
      setNewDomain('');
    }
  };

  const handleRemoveDomain = (domainToRemove: string) => {
    setDomains(domains.filter(domain => domain.value !== domainToRemove));
  };

  return (
    <div className="settings">
      <button
        className="bg-purple-500 text-white active:bg-purple-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
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
                  <div className="tabs">
                    <button onClick={() => setActiveTab('search')} className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}>Search Settings</button>
                    <button onClick={() => setActiveTab('domains')} className={`tab-button ${activeTab === 'domains' ? 'active' : ''}`}>Domain Filters</button>
                  </div>

                  {activeTab === 'search' && (
                    <div className="App">
                      <header className="App-header">
                        <ChatBox setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
                      </header>
                    </div>
                  )}
                  
                  {activeTab === 'domains' && (
                    <div className="mt-4">
                      <form onSubmit={handleAddDomain} className="flex gap-2 mb-4">
                        <input
                          type="text"
                          value={newDomain}
                          onChange={(e) => setNewDomain(e.target.value)}
                          placeholder="Enter domain (e.g., example.com)"
                          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                        <button
                          type="submit"
                          className="inline-flex justify-center rounded-md border border-transparent bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          Add Domain
                        </button>
                      </form>

                      <div className="flex flex-wrap gap-2">
                        {domains.map((domain, index) => (
                          <div
                            key={index}
                            className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm"
                          >
                            <span className="text-purple-700">{domain.value}</span>
                            <button
                              onClick={() => handleRemoveDomain(domain.value)}
                              className="ml-2 text-purple-400 hover:text-purple-600"
                            >
                              <CloseIcon className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                  )}
                </div>
                <div className="flex items-center justify-end p-3">
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