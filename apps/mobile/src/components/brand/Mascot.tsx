import type { FC } from 'react';
import type { SvgProps } from 'react-native-svg';

import YapiBase from '@/assets/mascot/yapi-base.svg';
import YapiCelebrating from '@/assets/mascot/yapi-celebrating.svg';
import YapiChef from '@/assets/mascot/yapi-chef.svg';
import YapiEcoWarrior from '@/assets/mascot/yapi-eco-warrior.svg';
import YapiHappy from '@/assets/mascot/yapi-happy.svg';
import YapiSad from '@/assets/mascot/yapi-sad.svg';
import YapiSleepy from '@/assets/mascot/yapi-sleepy.svg';
import YapiWithBag from '@/assets/mascot/yapi-with-bag.svg';

export type MascotState =
  | 'base'
  | 'happy'
  | 'sleepy'
  | 'celebrating'
  | 'sad'
  | 'chef'
  | 'eco-warrior'
  | 'with-bag';

const MAP: Record<MascotState, FC<SvgProps>> = {
  base: YapiBase,
  happy: YapiHappy,
  sleepy: YapiSleepy,
  celebrating: YapiCelebrating,
  sad: YapiSad,
  chef: YapiChef,
  'eco-warrior': YapiEcoWarrior,
  'with-bag': YapiWithBag,
};

export interface MascotProps {
  state?: MascotState;
  size?: number;
}

/**
 * Yapi the llama — La Yapa's mascot.
 * NOTE: SVGs are placeholders pending final illustrator artwork.
 */
export function Mascot({ state = 'happy', size = 160 }: MascotProps) {
  const Cmp = MAP[state];
  const height = Math.round((size / 200) * 240);
  return <Cmp width={size} height={height} />;
}
