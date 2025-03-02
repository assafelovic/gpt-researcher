import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import babel from '@rollup/plugin-babel';
import alias from '@rollup/plugin-alias';
import path from 'path';
import postcss from 'rollup-plugin-postcss';
import { terser } from 'rollup-plugin-terser';

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
    removeUseClientPlugin,
    alias({
      entries: [
        { find: '@', replacement: path.resolve(__dirname, 'src') }
      ]
    }),
    resolve({
      extensions: ['.js', '.jsx', '.ts', '.tsx']
    }),
    commonjs(),
    typescript({ tsconfig: './tsconfig.json' }),
    babel({
      babelHelpers: 'bundled',
      presets: [
        '@babel/preset-env',
        '@babel/preset-react',
        '@babel/preset-typescript'
      ],
      extensions: ['.js', '.jsx', '.ts', '.tsx'],
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
    'react-ga4'
  ]
};