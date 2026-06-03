module.exports = {
  root: true,
  extends: ['expo'],
  ignorePatterns: ['/dist/*', '/.expo/*'],
  overrides: [
    {
      // Metro/Babel/Jest configs are CommonJS Node scripts.
      files: ['*.config.js', 'babel.config.js', 'metro.config.js', 'jest.setup.js'],
      env: { node: true, jest: true },
    },
    {
      // Jest test files use jest/expect/describe/it globals.
      files: ['__tests__/**/*.{ts,tsx,js,jsx}', '**/*.test.{ts,tsx,js,jsx}'],
      env: { jest: true, node: true },
    },
  ],
};
