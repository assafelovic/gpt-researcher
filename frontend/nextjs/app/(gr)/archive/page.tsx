import type { Metadata } from 'next';
import ArchiveScreen from '../_components/ArchiveScreen';

export const metadata: Metadata = { title: 'Archive · GPT Researcher' };

export default function Page() {
  return <ArchiveScreen />;
}
