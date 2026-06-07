import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useAuthStore } from '@/auth/store';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

export default function BusinessProfile() {
  const { theme } = useTheme();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Mi negocio
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
          {user?.email}
        </Text>
        <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 24 }}>
          Configuración de negocio, equipo, payouts y onboarding llegan en próximas sesiones.
        </Text>
      </View>
      <View style={{ marginTop: 32 }}>
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
});
