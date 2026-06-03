import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { authApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useTheme } from '@/theme';

export default function ResetPasswordScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const { token } = useLocalSearchParams<{ token?: string }>();

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!token) {
      toast.show({ title: 'Enlace inválido o expirado.', tone: 'error' });
      return;
    }
    if (password.length < 8) {
      toast.show({ title: 'Tu contraseña debe tener mínimo 8 caracteres.', tone: 'warning' });
      return;
    }
    if (password !== confirm) {
      toast.show({ title: 'Las contraseñas no coinciden.', tone: 'warning' });
      return;
    }
    setSubmitting(true);
    try {
      await authApi.resetPassword({ token: String(token), new_password: password });
      toast.show({ title: 'Contraseña actualizada. Inicia sesión.', tone: 'success' });
      router.replace('/(auth)/login');
    } catch {
      toast.show({ title: 'El enlace ya no es válido. Pide otro.', tone: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <View style={styles.body}>
        <Text variant="body" style={{ color: theme.colors.textMuted }}>
          Elige una nueva contraseña.
        </Text>
        <Input
          label="Nueva contraseña"
          value={password}
          onChangeText={setPassword}
          variant="password"
          autoComplete="password-new"
          textContentType="newPassword"
        />
        <Input
          label="Confirmar contraseña"
          value={confirm}
          onChangeText={setConfirm}
          variant="password"
          autoComplete="password-new"
          textContentType="newPassword"
        />
        <Button variant="primary" size="lg" onPress={handleSubmit} loading={submitting} fullWidth>
          Actualizar contraseña
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  body: { gap: 16, paddingTop: 24 },
});
