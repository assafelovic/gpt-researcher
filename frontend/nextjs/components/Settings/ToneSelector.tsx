import React, { ChangeEvent } from 'react';

interface ToneSelectorProps {
  tone: string;
  onToneChange: (event: ChangeEvent<HTMLSelectElement>) => void;
}
export default function ToneSelector({ tone, onToneChange }: ToneSelectorProps) {
  return (
    <div className="form-group">
      <label htmlFor="tone" className="agent_question">Tone </label>
      <select 
        name="tone" 
        id="tone" 
        value={tone} 
        onChange={onToneChange} 
        className="form-control-static"
        required
      >
        <option value="Objective">Objective - Impartial and unbiased presentation of facts and findings</option>
        <option value="Formal">Formal - Adheres to academic standards with sophisticated language and structure</option>
        <option value="Analytical">Analytical - Critical evaluation and detailed examination of data and theories</option>
        <option value="Persuasive">Persuasive - Convincing the audience of a particular viewpoint or argument</option>
        <option value="Informative">Informative - Providing clear and comprehensive information on a topic</option>
        <option value="Explanatory">Explanatory - Clarifying complex concepts and processes</option>
        <option value="Descriptive">Descriptive - Detailed depiction of phenomena, experiments, or case studies</option>
        <option value="Critical">Critical - Judging the validity and relevance of the research and its conclusions</option>
        <option value="Comparative">Comparative - Juxtaposing different theories, data, or methods to highlight differences and similarities</option>
        <option value="Speculative">Speculative - Exploring hypotheses and potential implications or future research directions</option>
        <option value="Reflective">Reflective - Considering the research process and personal insights or experiences</option>
        <option value="Narrative">Narrative - Telling a story to illustrate research findings or methodologies</option>
        <option value="Humorous">Humorous - Light-hearted and engaging, usually to make the content more relatable</option>
        <option value="Optimistic">Optimistic - Highlighting positive findings and potential benefits</option>
        <option value="Pessimistic">Pessimistic - Focusing on limitations, challenges, or negative outcomes</option>
        <option value="Simple">Simple - Written for young readers, using basic vocabulary and clear explanations</option>
        <option value="Casual">Casual - Conversational and relaxed style for easy, everyday reading</option>
      </select>
    </div>
  );
}