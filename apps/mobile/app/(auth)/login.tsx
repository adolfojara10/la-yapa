import { Link } from 'expo-router';
import { useState } from 'react';
import { Keyboard, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { authApi } from '@/api';
import { useAppleSignIn } from '@/auth/useAppleSignIn';
import { useGoogleSignIn } from '@/auth/useGoogleSignIn';
import { useAuthStore } from '@/auth/store';
import { SocialButtons } from '@/components/auth/SocialButtons';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useTheme } from '@/theme';

export default function LoginScreen() {
  const { theme } = useTheme();
  const toast = useToast();
  const setAuthed = useAuthStore((s) => s.setAuthed);
  const { signIn: googleSignIn } = useGoogleSignIn();
  const apple = useAppleSignIn();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [appleLoading, setAppleLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) {
      toast.show({ title: 'Correo y contraseña requeridos.', tone: 'warning' });
      return;
    }
    Keyboard.dismiss();
    setSubmitting(true);
    try {
      const result = await authApi.login({ email: email.trim().toLowerCase(), password });
      await setAuthed(result.user, result.tokens);
      // Routing guard in app/_layout.tsx takes over from here.
    } catch {
      toast.show({ title: 'Correo o contraseña inválidos.', tone: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGoogle() {
    setGoogleLoading(true);
    try {
      const idToken = await googleSignIn();
      if (!idToken) return;
      const result = await authApi.loginWithGoogle({ id_token: idToken });
      await setAuthed(result.user, result.tokens);
    } catch {
      toast.show({ title: 'No pudimos iniciar sesión con Google.', tone: 'error' });
    } finally {
      setGoogleLoading(false);
    }
  }

  async function handleApple() {
    setAppleLoading(true);
    try {
      const credential = await apple.signIn();
      if (!credential) return;
      const result = await authApi.loginWithApple({
        identity_token: credential.identityToken,
        first_name: credential.firstName,
        last_name: credential.lastName,
      });
      await setAuthed(result.user, result.tokens);
    } catch {
      toast.show({ title: 'No pudimos iniciar sesión con Apple.', tone: 'error' });
    } finally {
      setAppleLoading(false);
    }
  }

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.colors.background }]}
    >
      <View style={styles.form}>
        <Input
          label="Correo"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          textContentType="emailAddress"
        />
        <Input
          label="Contraseña"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="password"
          textContentType="password"
        />
        <Link href="/(auth)/forgot-password" asChild>
          <Text variant="small" style={[styles.forgot, { color: theme.colors.primary }]}>
            ¿Olvidaste tu contraseña?
          </Text>
        </Link>
        <Button variant="primary" size="lg" onPress={handleLogin} loading={submitting} fullWidth>
          Iniciar sesión
        </Button>

        <View style={styles.divider}>
          <View style={[styles.dividerLine, { backgroundColor: theme.colors.border }]} />
          <Text variant="small" style={{ color: theme.colors.textMuted, marginHorizontal: 12 }}>
            o
          </Text>
          <View style={[styles.dividerLine, { backgroundColor: theme.colors.border }]} />
        </View>

        <SocialButtons
          onGoogle={handleGoogle}
          onApple={handleApple}
          googleLoading={googleLoading}
          appleLoading={appleLoading}
          appleAvailable={apple.isAvailable}
          disabled={submitting}
        />

        <View style={styles.signupRow}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            ¿Aún no tienes cuenta?{' '}
          </Text>
          <Link href="/(auth)/register" asChild>
            <Text variant="small" style={{ color: theme.colors.primary, fontWeight: '600' }}>
              Regístrate
            </Text>
          </Link>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  form: { gap: 16, paddingTop: 16 },
  forgot: { alignSelf: 'flex-end', textDecorationLine: 'underline' },
  divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 8 },
  dividerLine: { flex: 1, height: 1 },
  signupRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 8 },
});
