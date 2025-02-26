import React, { useState, useEffect } from "react";
import FileUpload from "../Settings/FileUpload";
import ToneSelector from "../Settings/ToneSelector";
import { useAnalytics } from "../../hooks/useAnalytics";
import { CloseIcon } from '@chakra-ui/icons';
import { ChatBoxSettings, Domain } from '@/types/data';

interface ResearchFormProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
  onFormSubmit?: (
    task: string,
    reportType: string,
    reportSource: string,
    domains: Domain[]
  ) => void;
}

export default function ResearchForm({
  chatBoxSettings,
  setChatBoxSettings,
  onFormSubmit,
}: ResearchFormProps) {
  const { trackResearchQuery } = useAnalytics();
  const [task, setTask] = useState("");
  const [newDomain, setNewDomain] = useState('');

  // Destructure necessary fields from chatBoxSettings
  let { report_type, report_source, tone } = chatBoxSettings;

  const [domains, setDomains] = useState<Domain[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('domainFilters');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  
  useEffect(() => {
    localStorage.setItem('domainFilters', JSON.stringify(domains));
    setChatBoxSettings(prev => ({
      ...prev,
      domains: domains
    }));
  }, [domains, setChatBoxSettings]);

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

  const onFormChange = (e: { target: { name: any; value: any } }) => {
    const { name, value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      [name]: value,
    }));
  };

  const onToneChange = (e: { target: { value: any } }) => {
    const { value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      tone: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onFormSubmit) {
      const updatedSettings = {
        ...chatBoxSettings,
        domains: domains // Make sure domains are included
      };
      setChatBoxSettings(updatedSettings);
      onFormSubmit(task, report_type, report_source, domains);
    }
  };

  return (
    <form
      method="POST"
      className="report_settings mt-3"
      onSubmit={handleSubmit}
    >
      <div className="form-group">
        <label htmlFor="report_type" className="agent_question">
          Report Type{" "}
        </label>
        <select
          name="report_type"
          value={report_type}
          onChange={onFormChange}
          className="form-control"
          required
        >
          <option value="research_report">
            Summary - Short and fast (~2 min)
          </option>
          <option value="deep">Deep Research Report</option>
          <option value="multi_agents">Multi Agents Report</option>
          <option value="detailed_report">
            Detailed - In depth and longer (~5 min)
          </option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="report_source" className="agent_question">
          Report Source{" "}
        </label>
        <select
          name="report_source"
          value={report_source}
          onChange={onFormChange}
          className="form-control"
          required
        >
          <option value="web">The Internet</option>
          <option value="local">My Documents</option>
          <option value="hybrid">Hybrid</option>
        </select>
      </div>

      {(chatBoxSettings.report_source === "web" || chatBoxSettings.report_source === "hybrid") && (
        <div className="mt-4">
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              placeholder="Filter by domain (e.g., techcrunch.com)"
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddDomain(e);
                }
              }}
            />
            <button
              type="button"
              onClick={handleAddDomain}
              className="inline-flex justify-center rounded-md border border-transparent bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              Add Domain
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {domains.map((domain, index) => (
              <div
                key={index}
                className="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm mb-3"
              >
                <span className="text-purple-700">{domain.value}</span>
                <button
                  type="button"
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

      {report_source === "local" || report_source === "hybrid" ? (
        <FileUpload />
      ) : null}
      
      <ToneSelector tone={tone} onToneChange={onToneChange} />
    </form>
  );
}
