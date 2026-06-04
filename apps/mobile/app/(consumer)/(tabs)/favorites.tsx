import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

/**
 * Stub. Real favorites list ships in Session 8 — for now, the heart on
 * each bag card persists server-side but there's no dedicated UI to
 * browse the set.
 */
export default function FavoritesScreen() {
  const { theme } = useTheme();
  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.body}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Tus favoritos
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 12 }}>
          La lista de negocios favoritos llega en la próxima sesión. Por ahora, toca el corazón en
          una bolsa para guardar tu negocio favorito.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  body: { flex: 1, justifyContent: 'center' },
});
