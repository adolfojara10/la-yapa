import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useGeocode } from '@/hooks/useGeocode';
import { useBusinessLocations } from '@/hooks/useBusinessResources';
import { useTheme } from '@/theme';

import type { BusinessLocation } from '@layapa/shared-types';

export default function BusinessLocationsScreen() {
  const { theme } = useTheme();
  const toast = useToast();
  const queryClient = useQueryClient();
  const locations = useBusinessLocations();

  const [editing, setEditing] = useState<BusinessLocation | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [phone, setPhone] = useState('');
  const [hoursText, setHoursText] = useState('Lun-Dom 08:00-18:00');
  const geocode = useGeocode(address);

  function resetForm() {
    setEditing(null);
    setName('');
    setAddress('');
    setLat(null);
    setLng(null);
    setPhone('');
    setHoursText('Lun-Dom 08:00-18:00');
  }

  function hydrate(location: BusinessLocation) {
    setEditing(location);
    setName(location.name);
    setAddress(location.address);
    setLat(location.lat);
    setLng(location.lng);
    setPhone(location.phone);
    setHoursText(location.hours_of_operation.default ?? '');
  }

  async function handleSave() {
    if (lat === null || lng === null) {
      toast.show({ title: 'Selecciona una direccion sugerida.', tone: 'warning' });
      return;
    }
    setSubmitting(true);
    try {
      if (editing) {
        await businessApi.updateLocation(editing.id, {
          name,
          address,
          lat,
          lng,
          phone,
          hours_of_operation: { default: hoursText },
        });
      } else {
        await businessApi.createLocation({
          name,
          address,
          lat,
          lng,
          phone,
          hours_of_operation: { default: hoursText },
        });
      }
      await queryClient.invalidateQueries({ queryKey: ['business-locations'] });
      resetForm();
      toast.show({ title: 'Ubicacion guardada.', tone: 'success' });
    } catch {
      toast.show({ title: 'No pudimos guardar la ubicacion.', tone: 'error' });
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleActive(location: BusinessLocation) {
    try {
      await businessApi.updateLocation(location.id, { is_active: !location.is_active });
      await queryClient.invalidateQueries({ queryKey: ['business-locations'] });
    } catch {
      toast.show({ title: 'No pudimos actualizar la ubicacion.', tone: 'error' });
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text variant="h2" style={{ color: theme.colors.text }}>
          Ubicaciones
        </Text>

        <View style={{ gap: 12 }}>
          {locations.data?.map((location) => (
            <View
              key={location.id}
              style={[
                styles.card,
                {
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                  borderRadius: theme.radii.lg,
                },
              ]}
            >
              <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
                {location.name}
              </Text>
              <Text variant="small" style={{ color: theme.colors.textMuted }}>
                {location.address}
              </Text>
              <View style={styles.row}>
                <View style={{ flex: 1 }}>
                  <Button variant="ghost" fullWidth onPress={() => hydrate(location)}>
                    Editar
                  </Button>
                </View>
                <View style={{ flex: 1 }}>
                  <Button variant="secondary" fullWidth onPress={() => void toggleActive(location)}>
                    {location.is_active ? 'Desactivar' : 'Activar'}
                  </Button>
                </View>
              </View>
            </View>
          ))}
        </View>

        <View style={{ gap: 12 }}>
          <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
            {editing ? 'Editar ubicacion' : 'Nueva ubicacion'}
          </Text>
          <Input label="Nombre" value={name} onChangeText={setName} />
          <Input label="Direccion" value={address} onChangeText={setAddress} />
          {geocode.suggestions.map((suggestion) => (
            <Pressable
              key={suggestion.id}
              onPress={() => {
                setAddress(suggestion.label);
                setLat(suggestion.lat);
                setLng(suggestion.lng);
              }}
              style={[
                styles.suggestion,
                {
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.border,
                  borderRadius: theme.radii.md,
                },
              ]}
            >
              <Text variant="small" style={{ color: theme.colors.text }}>
                {suggestion.label}
              </Text>
            </Pressable>
          ))}
          <Input label="Telefono" value={phone} onChangeText={setPhone} />
          <Input label="Horario" value={hoursText} onChangeText={setHoursText} />
          <Button variant="primary" loading={submitting} fullWidth onPress={handleSave}>
            {editing ? 'Guardar cambios' : 'Agregar ubicacion'}
          </Button>
          {editing ? (
            <Button variant="ghost" fullWidth onPress={resetForm}>
              Cancelar edicion
            </Button>
          ) : null}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { padding: 16, gap: 16, paddingBottom: 32 },
  card: { padding: 16, borderWidth: 1, gap: 8 },
  row: { flexDirection: 'row', gap: 10 },
  suggestion: { padding: 12, borderWidth: 1 },
});
