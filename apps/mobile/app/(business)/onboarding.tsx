import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { useAuthStore } from '@/auth/store';
import { pickDocumentAsset, pickImageAsset, uploadLabel } from '@/business/uploads';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useGeocode } from '@/hooks/useGeocode';
import { useTheme } from '@/theme';

import type {
  BusinessOnboardingPayload,
  BusinessType,
  BusinessTier,
  PayoutMethod,
  UploadAsset,
} from '@layapa/shared-types';

type Step = 0 | 1 | 2 | 3;

const BUSINESS_TYPES: { value: BusinessType; label: string }[] = [
  { value: 'restaurant', label: 'Restaurante' },
  { value: 'bakery', label: 'Panaderia' },
  { value: 'supermarket', label: 'Supermercado' },
  { value: 'hotel', label: 'Hotel' },
  { value: 'mercado', label: 'Mercado' },
  { value: 'farmer', label: 'Productor' },
];

function UploadField({
  label,
  file,
  onPick,
}: {
  label: string;
  file: UploadAsset | null;
  onPick: () => Promise<void>;
}) {
  const { theme } = useTheme();

  return (
    <View style={{ gap: 6 }}>
      <Text variant="small" style={{ color: theme.colors.textMuted }}>
        {label}
      </Text>
      <Button variant="ghost" onPress={() => void onPick()} fullWidth>
        {uploadLabel(file)}
      </Button>
    </View>
  );
}

export default function BusinessOnboardingScreen() {
  const { theme } = useTheme();
  const toast = useToast();
  const refreshMe = useAuthStore((s) => s.refreshMe);

  const [step, setStep] = useState<Step>(0);
  const [submitting, setSubmitting] = useState(false);

  const [tier, setTier] = useState<BusinessTier>('formal');
  const [businessType, setBusinessType] = useState<BusinessType>('bakery');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [website, setWebsite] = useState('');

  const [rucNumber, setRucNumber] = useState('');
  const [cedulaNumber, setCedulaNumber] = useState('');
  const [hasFoodHandling, setHasFoodHandling] = useState(true);
  const [rucDocument, setRucDocument] = useState<UploadAsset | null>(null);
  const [cedulaDocument, setCedulaDocument] = useState<UploadAsset | null>(null);
  const [permisoFuncionamiento, setPermisoFuncionamiento] = useState<UploadAsset | null>(null);
  const [arcsaDocument, setArcsaDocument] = useState<UploadAsset | null>(null);
  const [bankProof, setBankProof] = useState<UploadAsset | null>(null);
  const [selfieWithCedula, setSelfieWithCedula] = useState<UploadAsset | null>(null);
  const [businessPhoto, setBusinessPhoto] = useState<UploadAsset | null>(null);

  const [locationName, setLocationName] = useState('Local principal');
  const [address, setAddress] = useState('');
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [locationPhone, setLocationPhone] = useState('');
  const [hoursText, setHoursText] = useState('Lun-Dom 08:00-18:00');
  const geocode = useGeocode(address);

  const [payoutMethod, setPayoutMethod] = useState<PayoutMethod>('bank_transfer');
  const [accountHolder, setAccountHolder] = useState('');
  const [bankName, setBankName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [accountType, setAccountType] = useState('checking');
  const [deunaPhone, setDeunaPhone] = useState('');
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  function chooseSuggestion(suggestion: { label: string; lat: number; lng: number }) {
    setAddress(suggestion.label);
    setLat(suggestion.lat);
    setLng(suggestion.lng);
  }

  function canAdvance() {
    if (step === 0) return name.trim().length > 0;
    if (step === 1) return cedulaNumber.trim().length > 0;
    if (step === 2) return address.trim().length > 0 && lat !== null && lng !== null;
    return acceptedTerms && accountHolder.trim().length > 0;
  }

  async function handleSubmit() {
    if (lat === null || lng === null) {
      toast.show({ title: 'Selecciona una direccion valida.', tone: 'warning' });
      return;
    }
    const payload: BusinessOnboardingPayload = {
      name: name.trim(),
      business_type: businessType,
      tier,
      description: description.trim(),
      phone: phone.trim(),
      email: email.trim(),
      website: website.trim(),
      location_name: locationName.trim(),
      address: address.trim(),
      lat,
      lng,
      location_phone: locationPhone.trim(),
      hours_of_operation: { default: hoursText.trim() || 'Consultar con el negocio' },
      payout_method: payoutMethod,
      payout_frequency: 'weekly',
      account_holder: accountHolder.trim(),
      bank_name: bankName.trim(),
      account_number: accountNumber.trim(),
      account_type: accountType.trim(),
      deuna_phone: deunaPhone.trim(),
      cedula_number: cedulaNumber.trim(),
      ruc_number: rucNumber.trim(),
      has_food_handling: hasFoodHandling,
      food_safety_terms_accepted: acceptedTerms,
      ruc_document: rucDocument ?? undefined,
      cedula_document: cedulaDocument ?? undefined,
      selfie_with_cedula: selfieWithCedula ?? undefined,
      permiso_funcionamiento: permisoFuncionamiento ?? undefined,
      arcsa_document: arcsaDocument ?? undefined,
      bank_proof: bankProof ?? undefined,
      business_photo: businessPhoto ?? undefined,
    };

    setSubmitting(true);
    try {
      await businessApi.submitOnboarding(payload);
      await refreshMe();
      toast.show({ title: 'Solicitud enviada. Revisaremos tu cuenta pronto.', tone: 'success' });
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } }).response?.data
        ?.detail;
      toast.show({ title: detail ?? 'No pudimos enviar tu onboarding.', tone: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <View style={styles.progressRow}>
        {[0, 1, 2, 3].map((index) => (
          <View
            key={index}
            style={[
              styles.progressDot,
              {
                backgroundColor: index <= step ? theme.colors.primary : theme.colors.border,
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
              Tu negocio en La Yapa
            </Text>
            <View style={styles.choiceRow}>
              {(
                [
                  { value: 'formal', label: 'Empresa formal' },
                  { value: 'informal', label: 'Vendedor independiente' },
                ] as const
              ).map((option) => {
                const active = tier === option.value;
                return (
                  <Pressable
                    key={option.value}
                    onPress={() => setTier(option.value)}
                    style={[
                      styles.choiceCard,
                      {
                        borderColor: active ? theme.colors.primary : theme.colors.border,
                        backgroundColor: active ? theme.colors.primarySoft : theme.colors.surface,
                        borderRadius: theme.radii.lg,
                      },
                    ]}
                  >
                    <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                      {option.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Input label="Nombre comercial" value={name} onChangeText={setName} />
            <Input
              label="Descripcion"
              value={description}
              onChangeText={setDescription}
              multiline
            />
            <Input
              label="Telefono"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
            />
            <Input
              label="Email"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
            />
            <Input label="Sitio web (opcional)" value={website} onChangeText={setWebsite} />

            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              Tipo de negocio
            </Text>
            <View style={styles.chipRow}>
              {BUSINESS_TYPES.map((option) => {
                const active = businessType === option.value;
                return (
                  <Pressable
                    key={option.value}
                    onPress={() => setBusinessType(option.value)}
                    style={[
                      styles.chip,
                      {
                        borderColor: active ? theme.colors.primary : theme.colors.border,
                        backgroundColor: active ? theme.colors.primary : 'transparent',
                        borderRadius: theme.radii.full,
                      },
                    ]}
                  >
                    <Text
                      variant="small"
                      style={{ color: active ? theme.colors.textInverse : theme.colors.text }}
                    >
                      {option.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        ) : null}

        {step === 1 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              Documentos
            </Text>
            <Input
              label="Cedula"
              value={cedulaNumber}
              onChangeText={setCedulaNumber}
              keyboardType="number-pad"
            />
            {tier === 'formal' ? (
              <>
                <Input
                  label="RUC"
                  value={rucNumber}
                  onChangeText={setRucNumber}
                  keyboardType="number-pad"
                />
                <UploadField
                  label="RUC"
                  file={rucDocument}
                  onPick={async () => setRucDocument(await pickDocumentAsset())}
                />
                <UploadField
                  label="Cedula"
                  file={cedulaDocument}
                  onPick={async () => setCedulaDocument(await pickDocumentAsset())}
                />
                <UploadField
                  label="Permiso de funcionamiento"
                  file={permisoFuncionamiento}
                  onPick={async () => setPermisoFuncionamiento(await pickDocumentAsset())}
                />
                <UploadField
                  label="Comprobante bancario"
                  file={bankProof}
                  onPick={async () => setBankProof(await pickDocumentAsset())}
                />
              </>
            ) : (
              <>
                <UploadField
                  label="Cedula"
                  file={cedulaDocument}
                  onPick={async () => setCedulaDocument(await pickDocumentAsset())}
                />
                <UploadField
                  label="Selfie con cedula"
                  file={selfieWithCedula}
                  onPick={async () => setSelfieWithCedula(await pickImageAsset())}
                />
                <UploadField
                  label="Foto del negocio"
                  file={businessPhoto}
                  onPick={async () => setBusinessPhoto(await pickImageAsset())}
                />
              </>
            )}

            <Pressable
              onPress={() => setHasFoodHandling((current) => !current)}
              style={[
                styles.choiceCard,
                {
                  borderColor: hasFoodHandling ? theme.colors.primary : theme.colors.border,
                  backgroundColor: hasFoodHandling
                    ? theme.colors.primarySoft
                    : theme.colors.surface,
                  borderRadius: theme.radii.lg,
                },
              ]}
            >
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                Manipulo alimentos
              </Text>
            </Pressable>
            {tier === 'formal' && hasFoodHandling ? (
              <UploadField
                label="ARCSA"
                file={arcsaDocument}
                onPick={async () => setArcsaDocument(await pickDocumentAsset())}
              />
            ) : null}
          </View>
        ) : null}

        {step === 2 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              Ubicacion
            </Text>
            <Input label="Nombre del local" value={locationName} onChangeText={setLocationName} />
            <Input label="Direccion" value={address} onChangeText={setAddress} />
            {geocode.suggestions.length > 0 ? (
              <View style={{ gap: 8 }}>
                {geocode.suggestions.map((suggestion) => (
                  <Pressable
                    key={suggestion.id}
                    onPress={() => chooseSuggestion(suggestion)}
                    style={[
                      styles.suggestion,
                      {
                        borderColor: theme.colors.border,
                        backgroundColor: theme.colors.surface,
                        borderRadius: theme.radii.md,
                      },
                    ]}
                  >
                    <Text variant="small" style={{ color: theme.colors.text }}>
                      {suggestion.label}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : null}
            <Input
              label="Telefono del local"
              value={locationPhone}
              onChangeText={setLocationPhone}
              keyboardType="phone-pad"
            />
            <Input
              label="Horario"
              value={hoursText}
              onChangeText={setHoursText}
              helperText="Ejemplo: Lun-Dom 08:00-18:00"
            />
            {lat !== null && lng !== null ? (
              <Text variant="small" style={{ color: theme.colors.success }}>
                Ubicacion fijada ✓
              </Text>
            ) : null}
          </View>
        ) : null}

        {step === 3 ? (
          <View style={styles.stepBody}>
            <Text variant="h2" style={{ color: theme.colors.text }}>
              Cobros y seguridad alimentaria
            </Text>
            <View style={styles.choiceRow}>
              {(
                [
                  { value: 'bank_transfer', label: 'Transferencia' },
                  { value: 'de_una', label: 'DeUna' },
                ] as const
              ).map((option) => {
                const active = payoutMethod === option.value;
                return (
                  <Pressable
                    key={option.value}
                    onPress={() => setPayoutMethod(option.value)}
                    style={[
                      styles.choiceCard,
                      {
                        borderColor: active ? theme.colors.primary : theme.colors.border,
                        backgroundColor: active ? theme.colors.primarySoft : theme.colors.surface,
                        borderRadius: theme.radii.lg,
                      },
                    ]}
                  >
                    <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                      {option.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            <Input label="Titular" value={accountHolder} onChangeText={setAccountHolder} />
            {payoutMethod === 'bank_transfer' ? (
              <>
                <Input label="Banco" value={bankName} onChangeText={setBankName} />
                <Input
                  label="Numero de cuenta"
                  value={accountNumber}
                  onChangeText={setAccountNumber}
                  keyboardType="number-pad"
                />
                <Input label="Tipo de cuenta" value={accountType} onChangeText={setAccountType} />
              </>
            ) : (
              <Input
                label="Telefono DeUna"
                value={deunaPhone}
                onChangeText={setDeunaPhone}
                keyboardType="phone-pad"
              />
            )}

            <Pressable
              onPress={() => setAcceptedTerms((current) => !current)}
              style={[
                styles.choiceCard,
                {
                  borderColor: acceptedTerms ? theme.colors.primary : theme.colors.border,
                  backgroundColor: acceptedTerms ? theme.colors.primarySoft : theme.colors.surface,
                  borderRadius: theme.radii.lg,
                },
              ]}
            >
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                Acepto los terminos de seguridad alimentaria
              </Text>
            </Pressable>
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        {step < 3 ? (
          <Button
            variant="primary"
            size="lg"
            disabled={!canAdvance()}
            onPress={() => setStep((current) => (current + 1) as Step)}
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
            onPress={handleSubmit}
            fullWidth
          >
            Enviar para revision
          </Button>
        )}
        {step > 0 ? (
          <Button
            variant="ghost"
            onPress={() => setStep((current) => (current - 1) as Step)}
            fullWidth
          >
            Atras
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
  footer: { gap: 8, paddingBottom: 24 },
  choiceRow: { flexDirection: 'row', gap: 12 },
  choiceCard: { flex: 1, padding: 16, borderWidth: 1.5 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderWidth: 1.5 },
  suggestion: { padding: 12, borderWidth: 1 },
});
