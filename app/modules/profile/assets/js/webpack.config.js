const path = require('path');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'profile.bundle.js',
    path: path.resolve(__dirname, '../dist'),
  },
  resolve: {
    fallback: {
      "fs": false 
    }
  },
  mode: 'development',
};
