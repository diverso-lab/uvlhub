const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const tinymceDir = path.dirname(require.resolve('tinymce/package.json'));

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'dataset.bundle.js',
    path: path.resolve(__dirname, '../dist'),
  },
  resolve: {
    fallback: {},
  },
  mode: 'development',
  plugins: [
  new CopyWebpackPlugin({
    patterns: [
      { from: path.resolve(tinymceDir, 'skins'), to: 'skins' },
      { from: path.resolve(tinymceDir, 'icons'), to: 'icons' },
      { from: path.resolve(tinymceDir, 'themes'), to: 'themes' },
      { from: path.resolve(tinymceDir, 'plugins'), to: 'plugins' },
      { from: path.resolve(tinymceDir, 'models'), to: 'models' },
    ],
  }),
  ],
};
