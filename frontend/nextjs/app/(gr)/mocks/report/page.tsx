import MockRun from '../_components/MockRun';

export default function Page({ searchParams }: { searchParams: { followups?: string; tab?: string; figure?: string; chrome?: string } }) {
  const figure = searchParams.figure === undefined ? undefined : Number(searchParams.figure);
  return (
    <MockRun
      at={9999}
      withFollowUps={searchParams.followups === '1'}
      tab={searchParams.tab === 'chat' ? 'chat' : undefined}
      figure={Number.isInteger(figure) ? figure : undefined}
      chrome={searchParams.chrome !== '0'}
    />
  );
}
