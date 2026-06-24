const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'generator.bundle.js',
    path: path.resolve(__dirname, '../dist'),
    module: true
  },
  mode: 'development',
  devtool: 'source-map',

  experiments: {
    topLevelAwait: true,
    asyncWebAssembly: true,
    outputModule: true
  },

  resolve: {
    fallback: {
      fs: false,
      'fs/promises': false,
      child_process: false,
      crypto: false,
      url: false,
      vm: false,
      path: false
    },
    extensions: ['.mjs', '.js', '.json', '.wasm'],
    mainFields: ['browser', 'module', 'main'],
  },

  module: {
    rules: [
      { test: /\.wasm$/, type: 'webassembly/async' },
      { test: /\.m?js$/, resolve: { fullySpecified: false } },
    ]
  },

  plugins: [
    new webpack.IgnorePlugin({ resourceRegExp: /^node:/ })
  ]
};
