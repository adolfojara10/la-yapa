/**
 * Index route is a no-op: the AuthGuard in _layout.tsx redirects based on
 * auth state on every render, so we render nothing here. Keeping the file
 * around (instead of deleting it) means hitting `/` from a deep link or
 * cold launch lands on a valid route, then immediately gets redirected.
 */
import { View } from 'react-native';

export default function IndexRedirect() {
  return <View />;
}
