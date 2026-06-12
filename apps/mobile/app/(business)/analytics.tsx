import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Text } from '@/components/ui/Text';
import { useBusinessDashboard } from '@/hooks/useBusinessDashboard';
import { useTheme } from '@/theme';

function MetricCard({ label, value }: { label: string; value: string }) {
  const { theme } = useTheme();
  return (
    <View
      style={[
        styles.metricCard,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
          borderRadius: theme.radii.lg,
        },
      ]}
    >
      <Text variant="small" style={{ color: theme.colors.textMuted }}>
        {label}
      </Text>
      <Text variant="h2" style={{ color: theme.colors.text, marginTop: 8 }}>
        {value}
      </Text>
    </View>
  );
}

export default function BusinessAnalyticsScreen() {
  const { theme } = useTheme();
  const dashboard = useBusinessDashboard();
  const summary = dashboard.data;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.background }]}>
      <Text variant="h2" style={{ color: theme.colors.text }}>
        Resumen de hoy
      </Text>
      <View style={styles.grid}>
        <MetricCard label="Pedidos" value={String(summary?.today_orders_count ?? 0)} />
        <MetricCard label="Ingresos" value={`$${summary?.today_revenue ?? '0.00'}`} />
        <MetricCard label="Bolsas vendidas" value={String(summary?.today_bags_sold ?? 0)} />
        <MetricCard label="Activos" value={String(summary?.active_orders_count ?? 0)} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, padding: 24 },
  grid: { gap: 12, marginTop: 20 },
  metricCard: { padding: 16, borderWidth: 1 },
});
