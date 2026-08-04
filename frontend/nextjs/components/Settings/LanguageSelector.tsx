import React, { ChangeEvent } from "react";
import { ReportLanguage } from "@/types/data";


interface LanguageSelectorProps {
  language: ReportLanguage;
  onLanguageChange: (event: ChangeEvent<HTMLSelectElement>) => void;
}


export default function LanguageSelector({
  language,
  onLanguageChange,
}: LanguageSelectorProps) {
  return (
    <div className="form-group">
      <label htmlFor="language" className="agent_question">
        报告语言
      </label>
      <select
        id="language"
        name="language"
        value={language}
        onChange={onLanguageChange}
        className="form-control-static"
        required
      >
        <option value="Chinese (Simplified)">中文（简体）</option>
        <option value="English">English</option>
      </select>
    </div>
  );
}
