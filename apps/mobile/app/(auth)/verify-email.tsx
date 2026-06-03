import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { authApi } from '@/api';
import { useAuthStore } from '@/auth/store';
import { OtpInput } from '@/components/auth/OtpInput';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useTheme } from '@/theme';

const RESEND_COOLDOWN_SECONDS = 60;

export default function VerifyEmailScreen() {
  const { theme } = useTheme();
  const toast = useToast();
  const user = useAuthStore((s) => s.user);
  const refreshMe = useAuthStore((s) => s.refreshMe);
  const logout = useAuthStore((s) => s.logout);

  const [code, setCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  async function handleVerify(submitted: string) {
    if (!user?.email) return;
    setSubmitting(true);
    setError('');
    try {
      await authApi.verifyEmail({ email: user.email, code: submitted });
      await refreshMe();
      toast.show({ title: '¡Correo verificado!', tone: 'success' });
      // Routing guard transitions us to onboarding/consumer/business.
    } catch (err) {
      const detail = (err as { response?: { data?: { code?: string[] } } }).response?.data
        ?.code?.[0];
      if (detail === 'expired') {
        setError('Tu código venció. Pide uno nuevo.');
      } else if (detail === 'too_many_attempts') {
        setError('Demasiados intentos. Pide un código nuevo.');
      } else {
        setError('Código incorrecto.');
      }
      setCode('');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    if (!user?.email || cooldown > 0) return;
    try {
      await authApi.resendVerification({ email: user.email });
      toast.show({ title: 'Código reenviado.', tone: 'success' });
      setCooldown(RESEND_COOLDOWN_SECONDS);
      setError('');
    } catch {
      toast.show({ title: 'No pudimos reenviar el código.', tone: 'error' });
    }
  }

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <View style={styles.body}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Verifica tu correo
        </Text>
        <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
          Te enviamos un código de 6 dígitos a{' '}
          <Text variant="body" style={{ fontWeight: '600' }}>
            {user?.email ?? 'tu correo'}
          </Text>
          .
        </Text>

        <View style={styles.otpWrap}>
          <OtpInput value={code} onChange={setCode} onComplete={handleVerify} error={error} />
        </View>

        <Button
          variant="primary"
          size="lg"
          onPress={() => handleVerify(code)}
          loading={submitting}
          disabled={code.length !== 6}
          fullWidth
        >
          Verificar
        </Button>

        <Button variant="ghost" onPress={handleResend} disabled={cooldown > 0} fullWidth>
          {cooldown > 0 ? `Reenviar en ${cooldown}s` : 'Reenviar código'}
        </Button>

        <Button variant="ghost" onPress={logout} fullWidth>
          Usar otra cuenta
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  body: { gap: 12, paddingTop: 16 },
  otpWrap: { marginVertical: 24, alignItems: 'center' },
});
