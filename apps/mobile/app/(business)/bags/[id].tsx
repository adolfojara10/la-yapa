import { useLocalSearchParams } from 'expo-router';

import { BagFormScreen } from '@/business/BagFormScreen';

export default function EditBagScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const bagId = Array.isArray(params.id) ? params.id[0] : params.id;
  return <BagFormScreen bagId={bagId} />;
}
