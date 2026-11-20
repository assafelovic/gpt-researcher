import ResearchScreen from './ResearchScreen';

export default function Page({ params }: { params: { id: string } }) {
  return <ResearchScreen id={params.id} />;
}
