// /multi_agents/frontend/components/HumanFeedback.tsx

import React, { useState, useEffect } from 'react';

interface HumanFeedbackProps {
  websocket: WebSocket | null;
  onFeedbackSubmit: (feedback: string | null) => void;
  questionForHuman: boolean;
}

const HumanFeedback: React.FC<HumanFeedbackProps> = ({ questionForHuman, websocket, onFeedbackSubmit }) => {
  const [feedbackRequest, setFeedbackRequest] = useState<string | null>(null);
  const [userFeedback, setUserFeedback] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFeedbackSubmit(userFeedback === '' ? null : userFeedback);
    setFeedbackRequest(null);
    setUserFeedback('');
  };

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-2">Menschliches Feedback erforderlich</h3>
      <p className="mb-4">{questionForHuman}</p>
      <form onSubmit={handleSubmit}>
        <textarea
          className="w-full p-2 border rounded-md"
          value={userFeedback}
          onChange={(e) => setUserFeedback(e.target.value)}
          placeholder="Gib hier dein Feedback ein (oder leer lassen für 'nein')"
        />
        <button
          type="submit"
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          Feedback senden
        </button>
      </form>
    </div>
  );
};

export default HumanFeedback;
