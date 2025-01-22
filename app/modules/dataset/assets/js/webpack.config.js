const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const workingDir = process.env.WORKING_DIR || __dirname;

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
        {
          from: path.resolve(workingDir, './node_modules/tinymce/skins'),
          to: 'skins',
        },
        {
          from: path.resolve(workingDir, './node_modules/tinymce/icons'),
          to: 'icons',
        },
        {
          from: path.resolve(workingDir, './node_modules/tinymce/themes'),
          to: 'themes',
        },
        {
          from: path.resolve(workingDir, './node_modules/tinymce/plugins'),
          to: 'plugins',
        },
        {
          from: path.resolve(workingDir, './node_modules/tinymce/models'),
          to: 'models',
        },
      ],
    }),
  ],
};
