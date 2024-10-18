const path = require('path');

module.exports = {
  entry: {
    hubfile: './app/modules/hubfile/assets/js/scripts.js',  // Archivo de entrada para el módulo hubfile
  },
  output: {
    filename: '[name].bundle.js',  // Generará hubfile.bundle.js
    path: path.resolve(__dirname, 'app/modules/hubfile/assets/dist'),  // Ruta de salida
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',  // Para compatibilidad con ES6+
        },
      },
    ],
  },
  mode: 'development',
};
