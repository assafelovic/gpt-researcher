import HomeScreen from '../../_components/HomeScreen';
import type { BriefField } from '../../_components/Brief';
import type { SettingsTab } from '../../_components/preferences';

const fields: BriefField[] = ['report_type', 'report_source', 'tone', 'domains'];
const tabs: SettingsTab[] = ['research', 'mcp', 'documents', 'backend'];

export default function Page({ searchParams }: { searchParams: { open?: string; settings?: string } }) {
  const openField = fields.find((f) => f === searchParams.open);
  const settingsTab = tabs.find((t) => t === searchParams.settings);
  return <HomeScreen openField={openField} settingsTab={settingsTab} initialQuestion={openField ? 'How close are solid state batteries to mass production?' : ''} />;
}
