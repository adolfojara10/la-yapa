import { Link } from 'expo-router';
import { ScrollView, View } from 'react-native';

import { Logo } from '@/components/brand/Logo';
import { Mascot } from '@/components/brand/Mascot';
import { Button, Text } from '@/components/ui';
import { useTheme } from '@/theme';

export default function HomeScreen() {
  const { theme } = useTheme();
  return (
    <ScrollView
      contentContainerStyle={{
        flexGrow: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: theme.spacing[5],
        backgroundColor: theme.colors.background,
        gap: theme.spacing[4],
      }}
    >
      <Logo width={220} />
      <Mascot state="happy" size={180} />
      <Text variant="h2" align="center">
        Comida rescatada,{'\n'}planeta cuidado.
      </Text>
      <Text variant="body" color="textMuted" align="center">
        Bienvenido a La Yapa.
      </Text>
      <View style={{ width: '100%', maxWidth: 320, gap: theme.spacing[2] }}>
        <Link href="/design-system" asChild>
          <Button variant="primary" fullWidth>
            Ver design system
          </Button>
        </Link>
      </View>
    </ScrollView>
  );
}
