import React, { ChangeEvent } from 'react';

interface LayoutSelectorProps {
  layoutType: string;
  onLayoutChange: (event: ChangeEvent<HTMLSelectElement>) => void;
}

export default function LayoutSelector({ layoutType, onLayoutChange }: LayoutSelectorProps) {
  return (
    <div className="form-group">
      <label htmlFor="layoutType" className="agent_question">Layout-Typ </label>
      <select
        name="layoutType"
        id="layoutType"
        value={layoutType}
        onChange={onLayoutChange}
        className="form-control-static"
        required
      >
        <option value="research">Forschung - Klassisches Forschungs-Layout mit detaillierten Ergebnissen</option>
        <option value="copilot">Copilot - Nebeneinander angeordnete Forschungs- und Chat-Ansicht</option>
      </select>
    </div>
  );
}
