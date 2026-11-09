import MockRun from '../_components/MockRun';

export default function Page({ searchParams }: { searchParams: { chrome?: string } }) {
  return <MockRun scenario="failed" at={9999} chrome={searchParams.chrome !== '0'} />;
}
