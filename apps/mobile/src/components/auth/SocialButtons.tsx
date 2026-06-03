import { Apple, Chrome } from 'lucide-react-native';
import { Platform, StyleSheet, View } from 'react-native';

import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';

interface SocialButtonsProps {
  onGoogle: () => void;
  onApple: () => void;
  googleLoading?: boolean;
  appleLoading?: boolean;
  appleAvailable: boolean;
  disabled?: boolean;
}

export function SocialButtons({
  onGoogle,
  onApple,
  googleLoading = false,
  appleLoading = false,
  appleAvailable,
  disabled = false,
}: SocialButtonsProps) {
  return (
    <View style={styles.container}>
      <Button
        variant="secondary"
        onPress={onGoogle}
        loading={googleLoading}
        disabled={disabled}
        leftIcon={<Icon icon={Chrome} size={18} />}
        fullWidth
      >
        Continuar con Google
      </Button>
      {Platform.OS === 'ios' && appleAvailable ? (
        <Button
          variant="secondary"
          onPress={onApple}
          loading={appleLoading}
          disabled={disabled}
          leftIcon={<Icon icon={Apple} size={18} />}
          fullWidth
        >
          Continuar con Apple
        </Button>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 12 },
});
