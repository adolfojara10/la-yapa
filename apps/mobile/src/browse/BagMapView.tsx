import { StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

import { BagBottomSheet } from './BagBottomSheet';

interface Props {
  location: { lat: number; lng: number } | null;
}

export function BagMapView({ location }: Props) {
  const { theme } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.center}>
        <Text style={{ textAlign: 'center', padding: 20 }}>
          Mapbox has been temporarily disabled so you can build the app without a Mapbox token.
        </Text>
      </View>
      <BagBottomSheet bags={[]} onDismiss={() => {}} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
