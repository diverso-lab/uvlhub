const { merge } = require('webpack-merge');
const path = require('path');
const common = require(path.resolve(__dirname, '../../../../../core/webpack/webpack.common.js')); // Ruta al archivo común

module.exports = merge(common, {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'hubfile.bundle.js',
    path: path.resolve(__dirname, '../dist'),
  },
  resolve: {
    fallback: {
      "fs": false
    }
  },
});
