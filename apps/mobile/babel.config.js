module.exports = function (api) {
  api.cache(true);
  return {
    // babel-preset-expo (SDK 54) auto-includes the Worklets/Reanimated plugin
    // when `react-native-worklets` (Reanimated 4 peer) is installed.
    // Do NOT add `react-native-reanimated/plugin` here — that's the legacy v3
    // plugin and it conflicts with the v4 worklets transform.
    presets: ['babel-preset-expo'],
  };
};
