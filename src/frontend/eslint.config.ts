/*
 * MIT License
 *
 * Copyright (c) 2025 Mathieu Imfeld
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

import globals from "globals";
import tseslint from "typescript-eslint";
import tsParser from "@typescript-eslint/parser";
import stylistic from "@stylistic/eslint-plugin";
import { defineConfig } from "eslint/config";
import js from "@eslint/js";

export default defineConfig([
  // Ignore generated files
  { ignores: ["dist/**", "rollup.config.js"] },

  // Base recommended configs
  js.configs.recommended,
  tseslint.configs.strict,
  tseslint.configs.stylistic,
  tseslint.configs.recommendedTypeChecked,

  // Project rules
  {
    files: [
      "src/**/*.{js,mjs,cjs,ts,mts,cts}",
      "__fixtures__/**/*.ts",
      "__tests__/**/*.ts",
      "jest.config.ts",
      "eslint.config.ts",
    ],
    plugins: {
      "@stylistic": stylistic,
    },
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.jest,
      },
      parser: tsParser,
      ecmaVersion: 2023,
      sourceType: "module",
      parserOptions: {
        tsconfigRootDir: import.meta.dirname,
        project: ["./tsconfig.json"],
      },
    },
    rules: {
      "@stylistic/indent": ["error", 4],
      "@stylistic/no-trailing-spaces": "error",
      "@stylistic/quotes": ["warn", "single", { avoidEscape: true }],
      "@stylistic/array-bracket-newline": ["error", "consistent"],
      "@stylistic/array-element-newline": ["error", "consistent"],
      "@stylistic/arrow-parens": ["error", "as-needed"],
      "@stylistic/arrow-spacing": ["error", { before: true, after: true }],
      "@stylistic/block-spacing": ["error", "always"],
      "@stylistic/brace-style": ["error", "1tbs", { allowSingleLine: true }],
      eqeqeq: ["error", "always"],
      "eol-last": ["error", "always"],
    },
  },
]);
