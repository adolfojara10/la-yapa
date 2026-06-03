/** Jest config — keeps native-module mocks centralized. */
module.exports = {
  preset: 'jest-expo',
  testPathIgnorePatterns: ['/node_modules/', '/.expo/', '/dist/'],
  setupFiles: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@app/(.*)$': '<rootDir>/app/$1',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native|@react-native|@react-navigation|expo(nent)?|@expo(nent)?/.*|expo-modules-core|expo-router|@expo/.*|expo-secure-store|expo-auth-session|expo-apple-authentication|expo-crypto|expo-location|expo-constants|expo-web-browser|@gorhom/.*|lucide-react-native)',
  ],
};
