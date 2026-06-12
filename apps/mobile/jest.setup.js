/** Centralized native-module mocks for Jest. */

// expo-secure-store: in-memory mock
jest.mock('expo-secure-store', () => {
  const store = new Map();
  return {
    AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY: 'after_first_unlock_this_device_only',
    setItemAsync: jest.fn(async (key, value) => {
      store.set(key, value);
    }),
    getItemAsync: jest.fn(async (key) => store.get(key) ?? null),
    deleteItemAsync: jest.fn(async (key) => {
      store.delete(key);
    }),
    __reset: () => store.clear(),
  };
});

// expo-constants
jest.mock('expo-constants', () => ({
  expoConfig: { extra: { apiBaseUrl: 'http://test.local/api/v1' } },
}));

// expo-auth-session: never used in unit tests, but jest tries to resolve.
jest.mock('expo-auth-session', () => ({}));
jest.mock('expo-auth-session/providers/google', () => ({
  useIdTokenAuthRequest: () => [null, null, jest.fn()],
}));
jest.mock('expo-web-browser', () => ({
  maybeCompleteAuthSession: jest.fn(),
  openAuthSessionAsync: jest.fn(),
}));
jest.mock('expo-apple-authentication', () => ({
  isAvailableAsync: jest.fn(async () => false),
  signInAsync: jest.fn(),
  AppleAuthenticationScope: { FULL_NAME: 0, EMAIL: 1 },
}));
jest.mock('expo-location', () => ({
  requestForegroundPermissionsAsync: jest.fn(),
  getForegroundPermissionsAsync: jest.fn(async () => ({ status: 'undetermined' })),
  getCurrentPositionAsync: jest.fn(),
  Accuracy: { Balanced: 3 },
}));

// expo-camera: inert View + permission stub.
jest.mock('expo-camera', () => {
  const { View } = require('react-native');
  return {
    CameraView: View,
    useCameraPermissions: () => [{ granted: true, status: 'granted' }, jest.fn()],
  };
});

// expo-notifications: deterministic permission + token fixtures.
jest.mock('expo-notifications', () => ({
  getPermissionsAsync: jest.fn(async () => ({ status: 'undetermined' })),
  requestPermissionsAsync: jest.fn(async () => ({ status: 'granted' })),
  getExpoPushTokenAsync: jest.fn(async () => ({ data: 'ExponentPushToken[test-fixture]' })),
}));

// expo-image: render as a plain View so render-tree tests don't blow up.
jest.mock('expo-image', () => {
  const { View } = require('react-native');
  return { Image: View };
});

// react-native-qrcode-svg: inert View.
jest.mock('react-native-qrcode-svg', () => {
  const { View } = require('react-native');
  return { __esModule: true, default: View };
});

// expo-linking is used by checkout for deep-link return URL building.
jest.mock('expo-linking', () => ({
  createURL: (path, opts = {}) =>
    `layapa://${path}${opts.queryParams ? '?' + new URLSearchParams(opts.queryParams).toString() : ''}`,
  openURL: jest.fn(),
}));

// react-native-maps: inert primitives so map-dependent screens mount in Jest.
jest.mock('react-native-maps', () => {
  const { View } = require('react-native');
  return {
    __esModule: true,
    default: View,
    Marker: View,
    UrlTile: View,
  };
});

// @gorhom/bottom-sheet: simple passthrough so screens that mount it don't crash.
// We use forwardRef so imperative-handle .snapToIndex/.close are no-op
// functions instead of undefined.
jest.mock('@gorhom/bottom-sheet', () => {
  const React = require('react');
  const { View, FlatList, ScrollView } = require('react-native');
  const BottomSheet = React.forwardRef(function BottomSheetMock({ children }, ref) {
    React.useImperativeHandle(ref, () => ({
      snapToIndex: jest.fn(),
      snapToPosition: jest.fn(),
      close: jest.fn(),
      expand: jest.fn(),
    }));
    return React.createElement(View, null, children);
  });
  return {
    __esModule: true,
    default: BottomSheet,
    BottomSheetFlatList: FlatList,
    BottomSheetScrollView: ScrollView,
    BottomSheetView: View,
    BottomSheetTextInput: View,
  };
});
