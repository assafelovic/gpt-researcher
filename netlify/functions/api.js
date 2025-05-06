const { createProxyMiddleware } = require('http-proxy-middleware');
const serverless = require('serverless-http');
const express = require('express');
const app = express();

// Proxy all requests to the Python backend
const proxy = createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true,
  pathRewrite: {
    '^/.netlify/functions/api': '/'
  }
});

app.use('*', proxy);

// Export the serverless function
module.exports.handler = serverless(app);
