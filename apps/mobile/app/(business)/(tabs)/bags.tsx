import { useRouter } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import { Copy, Plus } from 'lucide-react-native';
import { RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { businessApi } from '@/api';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useToast } from '@/components/ui/Toast';
import { useBagTemplates, useBusinessBags } from '@/hooks/useBusinessResources';
import { useTheme } from '@/theme';

export default function BusinessBagsTab() {
  const { theme } = useTheme();
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const bags = useBusinessBags();
  const templates = useBagTemplates();

  async function handleDuplicate(id: string) {
    try {
      await businessApi.duplicateBag(id);
      await queryClient.invalidateQueries({ queryKey: ['business-bags'] });
      toast.show({ title: 'Bolsa duplicada y republicada.', tone: 'success' });
    } catch {
      toast.show({ title: 'No pudimos duplicar la bolsa.', tone: 'error' });
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={bags.isRefetching || templates.isRefetching}
            onRefresh={() => {
              bags.refetch();
              templates.refetch();
            }}
            tintColor={theme.colors.primary}
          />
        }
      >
        <View style={styles.header}>
          <Text variant="h2" style={{ color: theme.colors.text }}>
            Tus bolsas
          </Text>
          <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
            Crea nuevas publicaciones, re-lista las mas vendidas y reutiliza plantillas.
          </Text>
        </View>

        <Button
          variant="primary"
          size="lg"
          fullWidth
          leftIcon={<Plus size={18} color={theme.colors.textInverse} />}
          onPress={() => router.push('/(business)/bags/new')}
        >
          Nueva bolsa
        </Button>

        <View style={{ gap: 12 }}>
          <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
            Plantillas
          </Text>
          {templates.data?.length ? (
            templates.data.map((template) => (
              <View
                key={template.id}
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
                  {template.name}
                </Text>
                <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                  {template.title}
                </Text>
                <Button
                  variant="ghost"
                  onPress={() =>
                    router.push({
                      pathname: '/(business)/bags/new',
                      params: { templateId: template.id },
                    })
                  }
                  fullWidth
                >
                  Usar plantilla
                </Button>
              </View>
            ))
          ) : (
            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              Aun no tienes plantillas guardadas.
            </Text>
          )}
        </View>

        <View style={{ gap: 12 }}>
          <Text variant="bodyStrong" style={{ color: theme.colors.text }}>
            Publicadas
          </Text>
          {bags.data?.length ? (
            bags.data.map((bag) => (
              <View
                key={bag.id}
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
                  {bag.title}
                </Text>
                <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                  {bag.business_location_name} · {bag.quantity_available}/{bag.quantity_total}{' '}
                  disponibles
                </Text>
                <Text variant="small" style={{ color: theme.colors.textMuted, marginTop: 4 }}>
                  ${bag.sale_price} · retiro{' '}
                  {new Date(bag.pickup_window_start).toLocaleDateString('es-EC')}
                </Text>
                <View style={styles.actionsRow}>
                  <View style={{ flex: 1 }}>
                    <Button
                      variant="ghost"
                      fullWidth
                      leftIcon={<Copy size={16} color={theme.colors.primary} />}
                      onPress={() => void handleDuplicate(bag.id)}
                    >
                      Re-listar
                    </Button>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Button
                      variant="secondary"
                      fullWidth
                      disabled={!bag.can_edit}
                      onPress={() => router.push(`/(business)/bags/${bag.id}`)}
                    >
                      {bag.can_edit ? 'Editar' : 'Ya vendida'}
                    </Button>
                  </View>
                </View>
              </View>
            ))
          ) : (
            <Text variant="small" style={{ color: theme.colors.textMuted }}>
              Aun no has publicado bolsas.
            </Text>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { padding: 16, gap: 16, paddingBottom: 32 },
  header: { gap: 4 },
  card: { padding: 16, borderWidth: 1, gap: 10 },
  actionsRow: { flexDirection: 'row', gap: 10 },
});
