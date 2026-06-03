import { useRouter } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { authApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useTheme } from '@/theme';

export default function ForgotPasswordScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();

  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit() {
    if (!email) return;
    setSubmitting(true);
    try {
      await authApi.forgotPassword({ email: email.trim().toLowerCase() });
      setSent(true);
      toast.show({
        title: 'Si la cuenta existe, te enviamos un correo.',
        tone: 'success',
      });
    } catch {
      // Server is silent on success/failure — surface a generic message.
      toast.show({ title: 'No pudimos procesar la solicitud.', tone: 'error' });
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
          Te enviaremos un enlace para restablecer tu contraseña.
        </Text>
        <Input
          label="Correo"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          textContentType="emailAddress"
        />
        <Button
          variant="primary"
          size="lg"
          onPress={handleSubmit}
          loading={submitting}
          disabled={!email}
          fullWidth
        >
          {sent ? 'Reenviar' : 'Enviar enlace'}
        </Button>
        {sent ? (
          <Button variant="ghost" onPress={() => router.replace('/(auth)/login')} fullWidth>
            Volver a iniciar sesión
          </Button>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  body: { gap: 16, paddingTop: 24 },
});
