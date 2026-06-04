import { useRouter } from 'expo-router';
import { ChevronRight, ShoppingBag } from 'lucide-react-native';
import { Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useAuthStore } from '@/auth/store';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';

export default function ProfileScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          {user?.consumer_profile?.first_name ?? 'Mi perfil'}
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
          {user?.email}
        </Text>
      </View>

      <Pressable
        onPress={() => router.push('/(consumer)/orders')}
        style={({ pressed }) => [
          styles.row,
          {
            backgroundColor: theme.colors.surface,
            borderColor: theme.colors.border,
            borderRadius: theme.radii.lg,
            opacity: pressed ? 0.85 : 1,
          },
        ]}
      >
        <ShoppingBag size={20} color={theme.colors.text} />
        <Text variant="bodyStrong" style={{ color: theme.colors.text, flex: 1 }}>
          Mis pedidos
        </Text>
        <ChevronRight size={18} color={theme.colors.textMuted} />
      </Pressable>

      <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 24 }}>
        Edición de perfil, configuración de notificaciones y referidos llegan en una próxima sesión.
      </Text>

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
  header: { marginTop: 24, marginBottom: 16 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
    borderWidth: 1,
  },
});
