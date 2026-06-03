import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { Keyboard, Pressable, StyleSheet, View } from 'react-native';
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

type Role = 'consumer' | 'business_owner';

export default function RegisterScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const setAuthed = useAuthStore((s) => s.setAuthed);
  const { signIn: googleSignIn } = useGoogleSignIn();
  const apple = useAppleSignIn();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('consumer');
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [appleLoading, setAppleLoading] = useState(false);

  async function handleRegister() {
    if (!email || password.length < 8) {
      toast.show({
        title: 'Correo válido y contraseña de 8+ caracteres.',
        tone: 'warning',
      });
      return;
    }
    Keyboard.dismiss();
    setSubmitting(true);
    try {
      const result = await authApi.register({
        email: email.trim().toLowerCase(),
        password,
        role,
      });
      await setAuthed(result.user, result.tokens);
      router.replace('/(auth)/verify-email');
    } catch (err) {
      // Surface DRF field errors when present.
      const detail = (err as { response?: { data?: { email?: string[]; password?: string[] } } })
        .response?.data;
      const message = detail?.email?.[0] ?? detail?.password?.[0] ?? 'No pudimos crear tu cuenta.';
      toast.show({ title: message, tone: 'error' });
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
        <View style={styles.roleRow}>
          {(['consumer', 'business_owner'] as Role[]).map((r) => {
            const active = role === r;
            return (
              <Pressable
                key={r}
                onPress={() => setRole(r)}
                style={[
                  styles.rolePill,
                  {
                    borderRadius: theme.radii.full,
                    borderColor: active ? theme.colors.primary : theme.colors.border,
                    backgroundColor: active ? theme.colors.primary : 'transparent',
                  },
                ]}
              >
                <Text
                  variant="small"
                  style={{
                    color: active ? theme.colors.textInverse : theme.colors.text,
                    fontWeight: '600',
                  }}
                >
                  {r === 'consumer' ? 'Soy consumidor' : 'Soy negocio'}
                </Text>
              </Pressable>
            );
          })}
        </View>

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
          label="Contraseña (mín. 8 caracteres)"
          value={password}
          onChangeText={setPassword}
          variant="password"
          autoComplete="password-new"
          textContentType="newPassword"
        />
        <Button variant="primary" size="lg" onPress={handleRegister} loading={submitting} fullWidth>
          Crear cuenta
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

        <View style={styles.loginRow}>
          <Text variant="small" style={{ color: theme.colors.textMuted }}>
            ¿Ya tienes cuenta?{' '}
          </Text>
          <Link href="/(auth)/login" asChild>
            <Text variant="small" style={{ color: theme.colors.primary, fontWeight: '600' }}>
              Inicia sesión
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
  roleRow: { flexDirection: 'row', gap: 8 },
  rolePill: { flex: 1, paddingVertical: 10, alignItems: 'center', borderWidth: 1.5 },
  divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 8 },
  dividerLine: { flex: 1, height: 1 },
  loginRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 8 },
});
