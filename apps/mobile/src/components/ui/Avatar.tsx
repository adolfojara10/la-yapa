import { useState } from 'react';
import { Image, View } from 'react-native';

import { useTheme } from '@/theme';

import { Text } from './Text';

export type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

export interface AvatarProps {
  source?: { uri: string } | number;
  name?: string;
  size?: AvatarSize;
}

const SIZE: Record<AvatarSize, number> = { sm: 32, md: 40, lg: 56, xl: 80 };

function initials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}

export function Avatar({ source, name = '', size = 'md' }: AvatarProps) {
  const { theme } = useTheme();
  const [error, setError] = useState(false);
  const dimension = SIZE[size];
  const showImage = source && !error;

  return (
    <View
      style={{
        width: dimension,
        height: dimension,
        borderRadius: dimension / 2,
        backgroundColor: theme.colors.primarySoft,
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
      accessibilityRole="image"
      accessibilityLabel={name || 'avatar'}
    >
      {showImage ? (
        <Image
          source={source}
          onError={() => setError(true)}
          style={{ width: dimension, height: dimension }}
        />
      ) : (
        <Text
          variant={size === 'sm' ? 'caption' : size === 'xl' ? 'h2' : 'small'}
          style={{ color: theme.colors.primary }}
        >
          {initials(name) || '?'}
        </Text>
      )}
    </View>
  );
}
