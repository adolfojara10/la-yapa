// Metro config: SVG-as-component imports + monorepo React deduping.
// pnpm workspace resolution is handled by .npmrc (`node-linker=hoisted`),
// so no custom watchFolders / nodeModulesPaths are needed here.
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// ---------- SVG as React components ----------
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('react-native-svg-transformer/expo'),
};
config.resolver.assetExts = config.resolver.assetExts.filter((ext) => ext !== 'svg');
config.resolver.sourceExts = [...config.resolver.sourceExts, 'svg'];

// ---------- Force a single React copy across the bundle ----------
// In this pnpm monorepo, admin uses React 18 (Next 14) and mobile uses React
// 19 (RN 0.81). Some transitive deps (e.g. @tanstack/react-query whose peer
// range is ^18 || ^19) get pnpm-nested copies of `react@18.3.1` alongside the
// root-hoisted `react@19.1.0`. Metro's default resolver picks the nested one,
// producing "Invalid hook call / two copies of React" at runtime.
// Redirect every `react` / `react-dom` import to the mobile app's hoisted copy.
const reactRoot = path.resolve(__dirname, '../../node_modules/react');
const reactDomRoot = path.resolve(__dirname, '../../node_modules/react-dom');
config.resolver.extraNodeModules = {
  ...config.resolver.extraNodeModules,
  react: reactRoot,
  'react-dom': reactDomRoot,
};
const originalResolveRequest = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (moduleName === 'react' || moduleName.startsWith('react/')) {
    return context.resolveRequest(
      { ...context, originModulePath: path.join(reactRoot, 'package.json') },
      moduleName,
      platform,
    );
  }
  if (moduleName === 'react-dom' || moduleName.startsWith('react-dom/')) {
    return context.resolveRequest(
      { ...context, originModulePath: path.join(reactDomRoot, 'package.json') },
      moduleName,
      platform,
    );
  }
  if (originalResolveRequest) {
    return originalResolveRequest(context, moduleName, platform);
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;
