import MockRun from '../_components/MockRun';

export default function Page({ searchParams }: { searchParams: { at?: string; chrome?: string } }) {
  const at = searchParams.at === undefined ? undefined : Number(searchParams.at);
  return <MockRun scenario="review" at={Number.isFinite(at) ? at : undefined} chrome={searchParams.chrome !== '0'} />;
}
