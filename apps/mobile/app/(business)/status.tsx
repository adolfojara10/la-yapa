import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useAuthStore } from '@/auth/store';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useTheme } from '@/theme';
import { useRouter } from 'expo-router';

export default function BusinessStatusScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const summary = useAuthStore((s) => s.user?.business_summary);

  const status = summary?.status ?? 'pending';
  const title =
    status === 'pending'
      ? 'Tu cuenta está en revisión. Te avisaremos pronto. 🌱'
      : status === 'rejected'
        ? 'Necesitamos algunos ajustes antes de aprobar tu cuenta.'
        : 'Tu cuenta está suspendida temporalmente.';

  const body =
    status === 'rejected'
      ? summary?.rejection_reason || 'Revisa tus documentos y vuelve a enviarlos.'
      : status === 'suspended'
        ? 'Contacta al equipo de La Yapa para reactivar tu negocio.'
        : 'Nuestro equipo comercial está validando tu información.';

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        <Text variant="h2" align="center" style={{ color: theme.colors.text }}>
          {title}
        </Text>
        <Text
          variant="body"
          align="center"
          style={{ color: theme.colors.textMuted, marginTop: 12 }}
        >
          {body}
        </Text>
      </View>

      <View style={styles.footer}>
        {status === 'rejected' ? (
          <Button
            variant="primary"
            fullWidth
            onPress={() => router.replace('/(business)/onboarding')}
          >
            Corregir solicitud
          </Button>
        ) : null}
        <Button variant="ghost" fullWidth onPress={logout}>
          Cerrar sesion
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  content: { flex: 1, justifyContent: 'center' },
  footer: { gap: 8, paddingBottom: 24 },
});
