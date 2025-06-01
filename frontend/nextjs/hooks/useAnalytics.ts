import ReactGA from 'react-ga4';

interface ResearchData {
  query: string;
  report_type: string;
  report_source: string;
}

interface TrackResearchData {
  query: string;
  report_type: string;
  report_source: string;
}

export const useAnalytics = () => {
  const initGA = () => {
    if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID) {
      ReactGA.initialize(process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID);
    }
  };

  const trackResearchQuery = (data: TrackResearchData) => {
    ReactGA.event({
      category: 'Research',
      action: 'Submit Query',
      label: JSON.stringify({
        query: data.query,
        report_type: data.report_type,
        report_source: data.report_source
      })
    });
  };

  return {
    initGA,
    trackResearchQuery
  };
};