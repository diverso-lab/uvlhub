const path = require('path');

module.exports = {
  mode: process.env.FLASK_ENV === 'production' ? 'production' : 'development',
  devtool: process.env.FLASK_ENV === 'development' ? 'source-map' : false,
  optimization: {
    minimize: process.env.FLASK_ENV === 'production',
  },
};
