import { useLocalSearchParams } from 'expo-router';

import { BagFormScreen } from '@/business/BagFormScreen';

export default function NewBagScreen() {
  const params = useLocalSearchParams<{ templateId?: string }>();
  const templateId = Array.isArray(params.templateId) ? params.templateId[0] : params.templateId;
  return <BagFormScreen templateId={templateId} />;
}
