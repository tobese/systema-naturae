import eslint from '@eslint/js';
import htmlPlugin from 'eslint-plugin-html';
import globals from 'globals';

export default [
    {
        files: ['**/*.html'],
        plugins: {
            html: htmlPlugin,
        },
        languageOptions: {
            globals: {
                ...globals.browser,
            },
        },
        rules: {
            'no-unused-vars': 'warn',
            'no-undef': 'error',
            'no-unused-expressions': 'warn',
            'no-console': 'off',
            'no-var': 'error',
            'prefer-const': 'error',
            'no-debugger': 'warn',
            'no-alert': 'warn',
            'no-empty': 'warn',
            'no-implicit-globals': 'warn',
        },
    },
];