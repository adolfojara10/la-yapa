// Metro config: SVG-as-component imports.
// pnpm workspace resolution is handled by .npmrc (`node-linker=hoisted`),
// so no custom watchFolders / nodeModulesPaths are needed here.
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// ---------- SVG as React components ----------
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('react-native-svg-transformer/expo'),
};
config.resolver.assetExts = config.resolver.assetExts.filter((ext) => ext !== 'svg');
config.resolver.sourceExts = [...config.resolver.sourceExts, 'svg'];

module.exports = config;
