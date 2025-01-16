
const path = require('path');
const workingDir = process.env.WORKING_DIR || __dirname;

module.exports = {
  entry: path.resolve(__dirname, './scripts.js'),
  output: {
    filename: 'dataset.bundle.js',
    path: path.resolve(__dirname, '../dist'),
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'], // Load CSS
      },
      {
        test: /\.svg$/,
        use: ['raw-loader'], // Load SVGs as raw text
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
      },
    ],
  },
  resolve: {
    extensions: ['.js'],
    alias: {
      '@ckeditor': path.resolve(workingDir, 'node_modules/@ckeditor'),
    },
  },
  mode: 'development',
  devtool: 'source-map',
};
