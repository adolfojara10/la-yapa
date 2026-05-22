import { Heart, MapPin, ShoppingBag } from 'lucide-react-native';
import { useRef, useState } from 'react';
import { ScrollView, View } from 'react-native';

import { Logo } from '@/components/brand/Logo';
import { Mascot, type MascotState } from '@/components/brand/Mascot';
import {
  Avatar,
  Badge,
  BottomSheet,
  type BottomSheetRef,
  Button,
  Card,
  Icon,
  Input,
  Modal,
  Skeleton,
  Text,
  useToast,
} from '@/components/ui';
import { useTheme } from '@/theme';

const MASCOT_STATES: MascotState[] = [
  'happy',
  'sleepy',
  'celebrating',
  'sad',
  'chef',
  'eco-warrior',
  'with-bag',
];

export default function DesignSystemScreen() {
  const { theme, mode, toggle } = useTheme();
  const toast = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [emailErr, setEmailErr] = useState<string | undefined>(undefined);
  const sheetRef = useRef<BottomSheetRef>(null);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: theme.colors.background }}
      contentContainerStyle={{ padding: theme.spacing[4], gap: theme.spacing[6] }}
    >
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Logo width={140} />
        <Button variant="ghost" size="sm" onPress={toggle}>
          {mode === 'dark' ? 'Modo claro' : 'Modo oscuro'}
        </Button>
      </View>

      <Section title="Typography">
        <Text variant="h1">H1 — Poppins Bold</Text>
        <Text variant="h2">H2 — Poppins Semibold</Text>
        <Text variant="h3">H3 — Poppins Semibold</Text>
        <Text variant="body">Body — Inter Regular</Text>
        <Text variant="small" color="textMuted">
          Small — Inter Regular
        </Text>
        <Text variant="caption" color="textMuted">
          CAPTION — Inter Medium
        </Text>
      </Section>

      <Section title="Buttons">
        <View style={{ gap: theme.spacing[2] }}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button leftIcon={<Icon icon={Heart} tone="inverse" size={16} />}>With icon</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
        </View>
        <View style={{ flexDirection: 'row', gap: theme.spacing[2], marginTop: theme.spacing[2] }}>
          <Button size="sm">Sm</Button>
          <Button size="md">Md</Button>
          <Button size="lg">Lg</Button>
        </View>
      </Section>

      <Section title="Inputs">
        <Input label="Correo" placeholder="tu@correo.com" />
        <Input
          label="Correo (con error)"
          placeholder="tu@correo.com"
          value="invalido@"
          errorText={emailErr ?? 'Correo inválido'}
          onChangeText={() => setEmailErr(undefined)}
        />
        <Input
          label="Contraseña"
          variant="password"
          value={password}
          onChangeText={setPassword}
          placeholder="********"
          helperText="Mínimo 8 caracteres"
        />
        <Input variant="search" placeholder="Buscar negocios..." />
      </Section>

      <Section title="Badges">
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: theme.spacing[2] }}>
          <Badge tone="neutral">Neutral</Badge>
          <Badge tone="primary">Aprobado</Badge>
          <Badge tone="success">Activo</Badge>
          <Badge tone="warning">Pendiente</Badge>
          <Badge tone="error">Rechazado</Badge>
          <Badge tone="info">Info</Badge>
          <Badge tone="accent">Destacado</Badge>
        </View>
      </Section>

      <Section title="Avatars">
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: theme.spacing[3] }}>
          <Avatar size="sm" name="Sofía Pérez" />
          <Avatar size="md" name="Don Carlos" />
          <Avatar size="lg" name="María López" />
          <Avatar size="xl" name="Pedro Q" />
        </View>
      </Section>

      <Section title="Card · Skeleton">
        <Card>
          <View style={{ flexDirection: 'row', gap: theme.spacing[3], alignItems: 'center' }}>
            <Avatar name="Panadería La Esperanza" />
            <View style={{ flex: 1 }}>
              <Text variant="bodyStrong">Panadería La Esperanza</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Icon icon={MapPin} tone="textMuted" size={14} />
                <Text variant="small" color="textMuted">
                  Cuenca · 1.2 km
                </Text>
              </View>
            </View>
            <Badge tone="success">3 bolsas</Badge>
          </View>
        </Card>

        <Card>
          <View style={{ gap: theme.spacing[2] }}>
            <Skeleton height={20} width="60%" />
            <Skeleton height={16} width="40%" />
            <Skeleton height={80} radius={theme.radii.md} />
          </View>
        </Card>
      </Section>

      <Section title="Mascot — Yapi (placeholders)">
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={{ flexDirection: 'row', gap: theme.spacing[4] }}>
            {MASCOT_STATES.map((s) => (
              <View key={s} style={{ alignItems: 'center', gap: theme.spacing[1] }}>
                <Mascot state={s} size={120} />
                <Text variant="caption" color="textMuted">
                  {s}
                </Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </Section>

      <Section title="Overlays">
        <View style={{ gap: theme.spacing[2] }}>
          <Button variant="primary" onPress={() => setModalOpen(true)}>
            Abrir Modal
          </Button>
          <Button variant="secondary" onPress={() => sheetRef.current?.open()}>
            Abrir BottomSheet
          </Button>
          <Button
            variant="ghost"
            leftIcon={<Icon icon={ShoppingBag} tone="primary" size={16} />}
            onPress={() =>
              toast.show({
                title: '¡Reserva confirmada!',
                description: 'Tu bolsa está lista para retirar.',
                tone: 'success',
              })
            }
          >
            Mostrar Toast
          </Button>
        </View>
      </Section>

      <Modal
        visible={modalOpen}
        onRequestClose={() => setModalOpen(false)}
        title="¿Confirmar reserva?"
        description="Se cobrará $4.50 a tu método de pago predeterminado."
        footer={
          <View style={{ flexDirection: 'row', gap: theme.spacing[2], justifyContent: 'flex-end' }}>
            <Button variant="ghost" onPress={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              onPress={() => {
                setModalOpen(false);
                toast.show({ title: 'Reserva confirmada', tone: 'success' });
              }}
            >
              Confirmar
            </Button>
          </View>
        }
      >
        <Text variant="body" color="textMuted">
          Podrás retirar entre las 17:00 y 19:00 de hoy.
        </Text>
      </Modal>

      <BottomSheet ref={sheetRef} snapPoints={['40%', '85%']}>
        <Text variant="h3">Filtros</Text>
        <Text variant="small" color="textMuted">
          Ajusta la búsqueda según tu zona y preferencias.
        </Text>
        <View style={{ height: theme.spacing[4] }} />
        <Input label="Radio (km)" placeholder="3" keyboardType="numeric" />
        <View style={{ height: theme.spacing[2] }} />
        <Input label="Categoría" placeholder="Panadería, Restaurante..." />
        <View style={{ height: theme.spacing[4] }} />
        <Button onPress={() => sheetRef.current?.close()}>Aplicar</Button>
      </BottomSheet>
    </ScrollView>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const { theme } = useTheme();
  return (
    <View style={{ gap: theme.spacing[2] }}>
      <Text
        variant="caption"
        color="textMuted"
        style={{ letterSpacing: 1.5, textTransform: 'uppercase' }}
      >
        {title}
      </Text>
      {children}
    </View>
  );
}
