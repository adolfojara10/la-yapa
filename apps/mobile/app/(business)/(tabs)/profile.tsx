import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';

import { useAuthStore } from '@/auth/store';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

export default function BusinessProfile() {
  const { theme } = useTheme();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const summary = user?.business_summary;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Mi negocio
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
          {user?.email}
        </Text>
        {summary ? (
          <>
            <Text variant="bodyStrong" style={{ color: theme.colors.text, marginTop: 24 }}>
              {summary.name}
            </Text>
            <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
              {summary.business_type} · {summary.tier} · estado {summary.status}
            </Text>
          </>
        ) : null}
      </View>

      <View style={styles.actions}>
        <Button variant="secondary" onPress={() => router.push('/(business)/locations')} fullWidth>
          Gestionar ubicaciones
        </Button>
        <Button variant="ghost" onPress={() => router.push('/(business)/bags/new')} fullWidth>
          Crear nueva bolsa
        </Button>
        <Button variant="ghost" onPress={logout} fullWidth>
          Cerrar sesión
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  header: { marginTop: 24 },
  actions: { marginTop: 32, gap: 12 },
});
