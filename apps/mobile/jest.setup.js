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
jest.mock('expo-web-browser', () => ({ maybeCompleteAuthSession: jest.fn() }));
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

// expo-image: render as a plain View so render-tree tests don't blow up.
jest.mock('expo-image', () => {
  const { View } = require('react-native');
  return { Image: View };
});

// @rnmapbox/maps: pure inert mock — tests don't render the map screen.
jest.mock('@rnmapbox/maps', () => {
  const { View } = require('react-native');
  const passthrough = ({ children }) => children ?? null;
  return {
    __esModule: true,
    default: {
      setAccessToken: jest.fn(),
      StyleURL: { Light: 'mapbox://styles/mapbox/light-v11' },
      MapView: View,
      Camera: passthrough,
      UserLocation: passthrough,
      PointAnnotation: passthrough,
    },
    setAccessToken: jest.fn(),
    StyleURL: { Light: 'mapbox://styles/mapbox/light-v11' },
    MapView: View,
    Camera: passthrough,
    UserLocation: passthrough,
    PointAnnotation: passthrough,
  };
});

// @gorhom/bottom-sheet: simple passthrough so screens that mount it don't crash.
jest.mock('@gorhom/bottom-sheet', () => {
  const { View, FlatList, ScrollView } = require('react-native');
  return {
    __esModule: true,
    default: View,
    BottomSheetFlatList: FlatList,
    BottomSheetScrollView: ScrollView,
    BottomSheetView: View,
    BottomSheetTextInput: View,
  };
});
