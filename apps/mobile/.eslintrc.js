module.exports = {
  root: true,
  extends: ['expo'],
  ignorePatterns: ['/dist/*', '/.expo/*'],
  overrides: [
    {
      // Metro/Babel/Jest configs are CommonJS Node scripts.
      files: ['*.config.js', 'babel.config.js', 'metro.config.js'],
      env: { node: true },
    },
  ],
};
