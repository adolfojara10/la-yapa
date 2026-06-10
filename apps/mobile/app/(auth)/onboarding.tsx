/**
 * 4-step onboarding for new consumers: name → language → location → dietary.
 *
 * Implementation choice: a single screen with internal step state + horizontal
 * slide-style transitions. Splitting into 4 expo-router files would also work
 * but adds back-button complexity (we don't want users escaping with the OS
 * back button into a half-completed profile).
 *
 * Location permission step intentionally requests permission inline and stores
 * the device's current location only if granted; refusal is fine — we set
 * `default_location: null` and continue.
 */
import * as Location from 'expo-location';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { usersApi } from '@/api';
import { useAuthStore } from '@/auth/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useTheme } from '@/theme';

import type { LatLng, Locale } from '@layapa/shared-types';

const DIETARY_OPTIONS = [
  { key: 'vegetarian', label: 'Vegetariano' },
  { key: 'vegan', label: 'Vegano' },
  { key: 'gluten_free', label: 'Sin gluten' },
  { key: 'sin_lactosa', label: 'Sin lactosa' },
  { key: 'organico', label: 'Orgánico' },
];

type Step = 0 | 1 | 2 | 3;

export default function OnboardingScreen() {
  const { theme } = useTheme();
  const toast = useToast();
  const refreshMe = useAuthStore((s) => s.refreshMe);
  const user = useAuthStore((s) => s.user);

  const [step, setStep] = useState<Step>(0);
  const [firstName, setFirstName] = useState(user?.consumer_profile?.first_name ?? '');
  const [language, setLanguage] = useState<Locale>(user?.language ?? 'es');
  const [location, setLocation] = useState<LatLng | null>(
    user?.consumer_profile?.default_location ?? null,
  );
  const [locationDenied, setLocationDenied] = useState(false);
  const [dietary, setDietary] = useState<string[]>(
    user?.consumer_profile?.dietary_preferences ?? [],
  );
  const [submitting, setSubmitting] = useState(false);

  async function requestLocation() {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      setLocationDenied(true);
      return;
    }
    setLocationDenied(false);
    try {
      const pos = await Location.getCurrentPositionAsync({});
      setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    } catch {
      setLocationDenied(true);
    }
  }

  function toggleDietary(key: string) {
    setDietary((current) =>
      current.includes(key) ? current.filter((k) => k !== key) : [...current, key],
    );
  }

  async function handleFinish() {
    setSubmitting(true);
    try {
      await usersApi.patchMe({
        first_name: firstName.trim(),
        language,
        default_location: location,
        dietary_preferences: dietary,
      });
      await refreshMe();
      // Routing guard now sees onboarding_completed=true and pushes to (consumer).
    } catch {
      toast.show({ title: 'No pudimos guardar tu perfil.', tone: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  function canAdvance(): boolean {
    if (step === 0) return firstName.trim().length > 0;
    return true;
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.progressRow}>
        {[0, 1, 2, 3].map((i) => (
          <View
            key={i}
            style={[
              styles.progressDot,
              {
                backgroundColor: i <= step ? theme.colors.primary : theme.colors.border,
                borderRadius: theme.radii.full,
              },
            ]}
          />
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {step === 0 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              ¿Cómo te llamas?
            </Text>
            <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
              Lo usaremos para personalizar tu experiencia.
            </Text>
            <Input
              label="Nombre"
              value={firstName}
              onChangeText={setFirstName}
              autoCapitalize="words"
              autoComplete="given-name"
              textContentType="givenName"
            />
          </View>
        ) : null}

        {step === 1 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              Tu idioma
            </Text>
            <View style={styles.langRow}>
              {(['es', 'en'] as Locale[]).map((lang) => {
                const active = language === lang;
                return (
                  <Pressable
                    key={lang}
                    onPress={() => setLanguage(lang)}
                    style={[
                      styles.langCard,
                      {
                        borderRadius: theme.radii.lg,
                        borderColor: active ? theme.colors.primary : theme.colors.border,
                        backgroundColor: active ? theme.colors.primarySoft : theme.colors.surface,
                      },
                    ]}
                  >
                    <Text variant="h3" style={{ color: theme.colors.text }}>
                      {lang === 'es' ? 'Español' : 'English'}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        ) : null}

        {step === 2 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              Tu ubicación
            </Text>
            <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
              Te mostramos bolsas cerca de ti. Puedes cambiarlo después.
            </Text>
            {location ? (
              <Text variant="small" style={{ color: theme.colors.success, marginTop: 16 }}>
                Ubicación detectada ✓
              </Text>
            ) : locationDenied ? (
              <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 16 }}>
                Sin permiso de ubicación — sigue funcionando, pero verás resultados de toda la
                ciudad.
              </Text>
            ) : (
              <View style={{ marginTop: 16 }}>
                <Button variant="secondary" onPress={requestLocation} fullWidth>
                  Permitir ubicación
                </Button>
              </View>
            )}
          </View>
        ) : null}

        {step === 3 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              Preferencias
            </Text>
            <Text variant="body" style={{ color: theme.colors.textMuted, marginTop: 8 }}>
              Elige tus preferencias para personalizar tu feed (Opcional).
            </Text>
            <View style={styles.chipRow}>
              {DIETARY_OPTIONS.map((opt) => {
                const active = dietary.includes(opt.key);
                return (
                  <Pressable
                    key={opt.key}
                    onPress={() => toggleDietary(opt.key)}
                    style={[
                      styles.chip,
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
                      {opt.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        {step < 3 ? (
          <Button
            variant="primary"
            size="lg"
            disabled={!canAdvance()}
            onPress={() => setStep((s) => (s + 1) as Step)}
            fullWidth
          >
            Siguiente
          </Button>
        ) : (
          <Button
            variant="primary"
            size="lg"
            disabled={!canAdvance()}
            loading={submitting}
            onPress={handleFinish}
            fullWidth
          >
            Terminar
          </Button>
        )}
        {step > 0 ? (
          <Button variant="ghost" onPress={() => setStep((s) => (s - 1) as Step)} fullWidth>
            Atrás
          </Button>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, paddingHorizontal: 24 },
  progressRow: { flexDirection: 'row', gap: 8, paddingTop: 16, justifyContent: 'center' },
  progressDot: { width: 28, height: 6 },
  content: { flexGrow: 1, paddingTop: 24 },
  stepBody: { gap: 12 },
  langRow: { flexDirection: 'row', gap: 12, marginTop: 16 },
  langCard: { flex: 1, padding: 24, borderWidth: 1.5, alignItems: 'center' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 16 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderWidth: 1.5 },
  footer: { gap: 8, paddingBottom: 24 },
});
