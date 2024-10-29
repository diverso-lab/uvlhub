const path = require('path');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'downloadqueue.bundle.js',
    path: path.resolve(__dirname, '../dist'),
  },
  resolve: {
    fallback: {
      // The resolve.fallback in Webpack is used to provide replacements 
      // for (or ignore) Node.js modules that are not available in the browser
    }
  },
  mode: 'development',
};
