import MockRun from '../_components/MockRun';

export default function Page({ searchParams }: { searchParams: { at?: string; stopped?: string; chrome?: string } }) {
  const at = searchParams.at === undefined ? undefined : Number(searchParams.at);
  return <MockRun at={Number.isFinite(at) ? at : undefined} stopped={searchParams.stopped === '1'} chrome={searchParams.chrome !== '0'} />;
}
