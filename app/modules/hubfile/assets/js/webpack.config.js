const path = require('path');

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),  // Usar __dirname para obtener la ruta correcta
  output: {
    filename: 'hubfile.bundle.js',  // Nombre del bundle específico para este módulo
    path: path.resolve(__dirname, '../dist'),  // Guardar el bundle en app/modulo1/assets/dist
  },
  resolve: {
    fallback: {
      "fs": false  // Ignorar 'fs' en el navegador
    }
  },
  mode: 'development',
};
