import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from 'rollup-plugin-typescript2';
import babel from '@rollup/plugin-babel';
import { terser } from 'rollup-plugin-terser';
import json from '@rollup/plugin-json';
import postcss from 'rollup-plugin-postcss';
import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';
import imageTransformPlugin from './src/utils/imageTransformPlugin';

const removeUseClientPlugin = {
  name: 'remove-use-client',
  transform(code) {
    return code.replace(/"use client";?/, '');
  }
};

export default {
  input: 'src/index.ts',
  output: [
    {
      file: 'dist/index.js',
      format: 'cjs',
      sourcemap: true
    },
    {
      file: 'dist/index.esm.js',
      format: 'esm',
      sourcemap: true
    }
  ],
  plugins: [
    postcss({
      plugins: [
        tailwindcss('./tailwind.config.ts'),
        autoprefixer,
      ],
      inject: true, // This will automatically inject CSS
      minimize: true,
      extract: false // Keep CSS in JS for easier consumption
    }),
    json(), // Add this plugin to handle JSON files   
    removeUseClientPlugin,
    imageTransformPlugin(),
    resolve({
      extensions: ['.js', '.jsx', '.ts', '.tsx'],
      browser: true, // Ensures it only includes browser-compatible modules
      preferBuiltins: false // Prevents bundling Node.js modules
    }),
    commonjs(),
    typescript({
      tsconfig: './tsconfig.lib.json',
      useTsconfigDeclarationDir: true,
      clean: true
    }),
    babel({
      babelHelpers: 'bundled',
      configFile: './.babelrc.build.json',
      extensions: ['.js', '.jsx', '.ts', '.tsx'],
      presets: [
        '@babel/preset-env',
        '@babel/preset-react',
        ['@babel/preset-typescript', { allowNamespaces: true, onlyRemoveTypeImports: true }]
      ],
      plugins: [
        ['@babel/plugin-transform-typescript', { allowNamespaces: true }]
      ],
      exclude: 'node_modules/**'
    }),
    terser()
  ],
  external: [
    'next',
    'react', 
    'react-dom',
    'react-hot-toast',
    'remark',
    'remark-html',
    '@langchain/langgraph-sdk',
     // Ensure all Node.js built-in modules are excluded 
     'fs', 'path', 'crypto', 'util', 'http', 'https', 'zlib', 'stream', 'url', 'assert', 'tty'
  ]
};