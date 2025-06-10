// const path = require('path');

// module.exports = {
//   entry: path.resolve(__dirname, './scripts.js'),
//   output: {
//     filename: 'generator.bundle.js',
//     path: path.resolve(__dirname, '../dist'),
//   },
//   resolve: {
//     fallback: {
//       fs: false,
//       child_process: false
//     }
//   },
//   mode: 'development',
// };



const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'generator.bundle.js',
    path: path.resolve(__dirname, '../dist'),
  },
  mode: 'development',
  devtool: 'source-map',
  experiments: {
    topLevelAwait: true,
    asyncWebAssembly: true,
  },
  resolve: {
    alias: {
      pyodide: path.resolve(__dirname, 'pyodide')
    },
    fallback: {
      fs: false,
      'fs/promises': false,
      child_process: false,
      crypto: false,
      url: false,
      vm: false,
      path: false,
    },
    extensions: ['.mjs', '.js', '.json', '.wasm'],
    mainFields: ['browser','module','main'],
  },
  module: {
    rules: [
      { test: /\.wasm$/, type: 'webassembly/async' },
      { test: /\.mjs$/, resolve: { fullySpecified: false } },
    ]
  },
  plugins: [
    // <-- Aquí ignoramos TODO import que comience por "node:"
    new webpack.IgnorePlugin({
      resourceRegExp: /^node:/,
    }),
  ],
};
