import { Link } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

export default function WelcomeScreen() {
  const { theme } = useTheme();
  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.hero}>
        <Text variant="h1" style={[styles.title, { color: theme.colors.primary }]}>
          La Yapa
        </Text>
        <Text variant="h3" style={[styles.tagline, { color: theme.colors.text }]}>
          Comida rescatada, planeta cuidado.
        </Text>
        <Text variant="body" style={[styles.body, { color: theme.colors.textMuted }]}>
          Encuentra bolsas de comida con hasta 70% de descuento de tus restaurantes favoritos.
        </Text>
      </View>

      <View style={styles.actions}>
        <Link href="/(auth)/register" asChild>
          <Button variant="primary" size="lg" fullWidth>
            Crear cuenta
          </Button>
        </Link>
        <Link href="/(auth)/login" asChild>
          <Button variant="ghost" size="lg" fullWidth>
            Ya tengo cuenta
          </Button>
        </Link>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24, justifyContent: 'space-between' },
  hero: { flex: 1, justifyContent: 'center', gap: 12 },
  title: { fontSize: 48, lineHeight: 56 },
  tagline: { marginTop: 4 },
  body: { marginTop: 8 },
  actions: { gap: 12, paddingBottom: 24 },
});
