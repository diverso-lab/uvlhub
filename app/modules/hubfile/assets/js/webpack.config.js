const path = require('path');
const webpack = require('webpack');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'hubfile.bundle.js',
    path: path.resolve(__dirname, '../dist'),
  },
  resolve: {
    fallback: {
      fs: false,
    },
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'string-replace-loader',
        options: {
          search: 'console.error(\'Error: \' + e);',
          replace: '', // Elimina esta línea
        },
      },
    ],
  }
};
