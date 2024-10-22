const path = require('path');
const dotenv = require('dotenv');

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

console.log('FLASK_ENV:', process.env.FLASK_ENV);

module.exports = {
  mode: process.env.FLASK_ENV === 'production' ? 'production' : 'development',

  devtool: process.env.FLASK_ENV === 'development' ? 'source-map' : false,

  optimization: {
    minimize: process.env.FLASK_ENV === 'production',
  },
  
};
