const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'generator.bundle.js',
    path: path.resolve(__dirname, '../dist'),
<<<<<<< HEAD
    module: true
=======
    module: true,        // <-- Emitimos un ES module
>>>>>>> cf1220c93be57f9d958e0ea590c58c50617ba390
  },
  mode: 'development',
  devtool: 'source-map',

  experiments: {
    topLevelAwait: true,
    asyncWebAssembly: true,
<<<<<<< HEAD
    outputModule: true
  },

  resolve: {
    alias: {
      pyodide: path.resolve(__dirname, '../../../../static/pyodide')
    },
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
=======
    outputModule: true,  // <-- Esto + output.module: true
  },

  resolve: {
    alias: { pyodide: path.resolve(__dirname, '../../../../static/pyodide') },
    fallback: { fs: false, 'fs/promises': false, child_process: false,
                crypto: false, url: false, vm: false, path: false },
    extensions: ['.mjs','.js','.json','.wasm'],
    mainFields: ['browser','module','main'],
>>>>>>> cf1220c93be57f9d958e0ea590c58c50617ba390
  },

  module: {
    rules: [
      { test: /\.wasm$/, type: 'webassembly/async' },
<<<<<<< HEAD
      { test: /\.m?js$/, resolve: { fullySpecified: false } },
    ]
  },

  plugins: [
    new webpack.IgnorePlugin({ resourceRegExp: /^node:/ })
  ]
};
=======
      { test: /\.mjs$/, resolve: { fullySpecified: false } },
    ]
  },
  plugins: [
    new webpack.IgnorePlugin({ resourceRegExp: /^node:/ })
  ]
};

>>>>>>> cf1220c93be57f9d958e0ea590c58c50617ba390
