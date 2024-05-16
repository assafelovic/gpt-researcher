export default function webpack(config, isServer) {
  // See https://webpack.js.org/configuration/resolve/#resolvealias
  config.resolve.alias = {
    ...config.resolve.alias,
    sharp$: false,
    "onnxruntime-node$": false,
  };
  config.resolve.fallback = {
    aws4: false,
  };
  config.module.rules.push({
    test: /\.node$/,
    loader: "node-loader",
  });
  if (isServer) {
    config.ignoreWarnings = [{ module: /opentelemetry/ }];
  }
  return config;
}
