const path = require("path");

module.exports = {
    entry: path.resolve(__dirname, "./scripts.js"),
    output: {
        filename: "statistics.bundle.js",
        path: path.resolve(__dirname, "../dist"),
        module: true,
    },
    experiments: {
        outputModule: true,
    },
    resolve: {
        fallback: { fs: false },
    },
    mode: "development",
    devtool: "source-map",
};
