import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from 'rollup-plugin-typescript2';
import babel from '@rollup/plugin-babel';
// import alias from '@rollup/plugin-alias';
// import path from 'path';
import postcss from 'rollup-plugin-postcss';
import { terser } from 'rollup-plugin-terser';
import json from '@rollup/plugin-json';

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
    json(), // Add this plugin to handle JSON files   
    removeUseClientPlugin,
    // alias({
    //   entries: [
    //     { find: '@', replacement: path.resolve(__dirname, 'src') }
    //   ]
    // }),
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
    postcss({
      extensions: ['.css'],
      minimize: true,
      extract: 'css/styles.css'
    }),
    terser()
  ],
  external: [
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