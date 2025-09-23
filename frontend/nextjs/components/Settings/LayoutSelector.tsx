import React, { ChangeEvent } from 'react';

interface LayoutSelectorProps {
  layoutType: string;
  onLayoutChange: (event: ChangeEvent<HTMLSelectElement>) => void;
}

export default function LayoutSelector({ layoutType, onLayoutChange }: LayoutSelectorProps) {
  return (
    <div className="form-group">
      <label htmlFor="layoutType" className="agent_question">Layout Type </label>
      <select 
        name="layoutType" 
        id="layoutType" 
        value={layoutType} 
        onChange={onLayoutChange} 
        className="form-control-static"
        required
      >
        <option value="research">Research - Traditional research layout with detailed results</option>
        <option value="copilot">Copilot - Side-by-side research and chat interface</option>
      </select>
    </div>
  );
} 