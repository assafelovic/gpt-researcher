import React, { ChangeEvent } from 'react';

interface ToneSelectorProps {
  tone: string;
  onToneChange: (event: ChangeEvent<HTMLSelectElement>) => void;
}
export default function ToneSelector({ tone, onToneChange }: ToneSelectorProps) {
  return (
    <div className="form-group">
      <label htmlFor="tone" className="agent_question">Ton </label>
      <select
        name="tone"
        id="tone"
        value={tone}
        onChange={onToneChange}
        className="form-control-static"
        required
      >
        <option value="Objective">Objektiv - Unparteiische und ausgewogene Darstellung von Fakten und Ergebnissen</option>
        <option value="Formal">Formal - Entspricht akademischen Standards mit anspruchsvoller Sprache und Struktur</option>
        <option value="Analytical">Analytisch - Kritische Auswertung und detaillierte Betrachtung von Daten und Theorien</option>
        <option value="Persuasive">Überzeugend - Betont eine bestimmte Perspektive oder Argumentation</option>
        <option value="Informative">Informativ - Klare und umfassende Informationen zu einem Thema</option>
        <option value="Explanatory">Erklärend - Verdeutlicht komplexe Konzepte und Prozesse</option>
        <option value="Descriptive">Beschreibend - Detaillierte Darstellung von Phänomenen, Experimenten oder Fallstudien</option>
        <option value="Critical">Kritisch - Bewertet die Gültigkeit und Relevanz der Forschung und ihrer Schlussfolgerungen</option>
        <option value="Comparative">Vergleichend - Stellt Unterschiede und Gemeinsamkeiten verschiedener Theorien, Daten oder Methoden gegenüber</option>
        <option value="Speculative">Spekulativ - Untersucht Hypothesen und mögliche zukünftige Entwicklungen</option>
        <option value="Reflective">Reflektierend - Betrachtet den Forschungsprozess und persönliche Einsichten</option>
        <option value="Narrative">Narrativ - Erzählt eine Geschichte, um Forschungsergebnisse oder Methoden zu veranschaulichen</option>
        <option value="Humorous">Humorvoll - Locker und unterhaltsam, um Inhalte zugänglicher zu machen</option>
        <option value="Optimistic">Optimistisch - Hebt positive Ergebnisse und mögliche Vorteile hervor</option>
        <option value="Pessimistic">Pessimistisch - Fokussiert auf Einschränkungen, Herausforderungen oder negative Ergebnisse</option>
        <option value="Simple">Einfach - Für junge Leser geschrieben, mit einfacher Sprache und klaren Erklärungen</option>
        <option value="Casual">Locker - Gesprächig und entspannt für leichtes Alltagslesen</option>
      </select>
    </div>
  );
}
