import React, { useState, useEffect } from "react";
import FileUpload from "../Settings/FileUpload";
import ToneSelector from "../Settings/ToneSelector";
import { useAnalytics } from "../../hooks/useAnalytics";
import { ChatBoxSettings, Domain } from '@/types/data';

interface ResearchFormProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
  onFormSubmit?: (
    task: string,
    reportType: string,
    reportSource: string,
  ) => void;
  defaultReportType: string;
}

export default function ResearchForm({
  chatBoxSettings,
  setChatBoxSettings,
  onFormSubmit,
  defaultReportType,
}: ResearchFormProps) {
  const { trackResearchQuery } = useAnalytics();
  const [task, setTask] = useState(""); // You can use this to capture any specific task data if needed

  // Destructure necessary fields from chatBoxSettings
  let { report_type, report_source, tone } = chatBoxSettings;

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
        onFormSubmit(task, report_type, report_source); // Trigger the onFormSubmit prop when form is submitted
      trackResearchQuery({ query: task, report_type, report_source });
    } else {
      console.warn("onFormSubmit is not defined");
    }
  };

  useEffect(() => {
    // Set default report type only if report_type is empty (initial mount)
    if (!chatBoxSettings.report_type) {
      setChatBoxSettings((prevSettings) => ({
        ...prevSettings,
        report_type: defaultReportType,
      }));
    }
  }, [defaultReportType, setChatBoxSettings, chatBoxSettings.report_type]);

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

          <option value="multi_agents">Multi Agents Report</option>
          <option value="research_report">
            Summary - Short and fast (~2 min)
          </option>
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
      {/* Conditional file upload if the report source is 'local' or 'hybrid' */}
      {report_source === "local" || report_source === "hybrid" ? (
        <FileUpload />
      ) : null}
      {/* ToneSelector for changing the tone */}
      <ToneSelector tone={tone} onToneChange={onToneChange} />

      {/** TODO: move the below to its own component */}
      {(chatBoxSettings.report_source === "web" || chatBoxSettings.report_source === "hybrid") && (
        <div className="mt-4 domain_filters">
          <div className="flex gap-2 mb-4">
          <label htmlFor="domain_filters" className="agent_question">
          Filter by domain{" "}
        </label>
            <input
              type="text"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              placeholder="Filter by domain (e.g., techcrunch.com)"
              className="input-static"
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
              className="button-static"
            >
              Add Domain
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {domains.map((domain, index) => (
              <div
                key={index}
                className="domain-tag-static"
              >
                <span className="domain-text-static">{domain.value}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveDomain(domain.value)}
                  className="domain-button-static"
                >
                  X
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </form>
  );
}
