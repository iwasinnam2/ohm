import { FlatCompat } from "@eslint/eslintrc";

// eslint-config-next 15.5 ships only legacy eslintrc-style configs (no flat
// config, no `exports` map), so ESLint 9 flat config must bridge through
// FlatCompat — the documented Next 15 setup. Revisit on the Next 16 upgrade,
// which ships native flat configs.
const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"],
  },
];

export default eslintConfig;
