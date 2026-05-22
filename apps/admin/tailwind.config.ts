import type { Config } from 'tailwindcss';
import animate from 'tailwindcss-animate';

import { palette, radii, spacing, typeScale } from '@layapa/ui';

/**
 * Tailwind config that mirrors the design tokens from `@layapa/ui`.
 *
 * Brand colors are exposed two ways:
 *   • As raw palette utilities (`bg-verde-paramo`) — useful for marketing pages.
 *   • As semantic utilities backed by CSS variables (`bg-background`, `text-foreground`, …)
 *     so light/dark mode swaps just by toggling the `.dark` class.
 */
const semantic = (name: string) => `rgb(from var(--color-${name}) r g b / <alpha-value>)`;

// Tailwind's `colors` only accepts hex/rgb/oklch/var(). We use `var()` directly because
// the values in `tokens.ts` are plain hex (not channel triplets), so opacity modifiers
// won't work — that's the tradeoff for a single source of truth without preprocessing.
const cssVar = (name: string) => `var(--color-${name})`;

const config: Config = {
  darkMode: ['class', '[data-theme="dark"]'],
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    '../../packages/ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ----- Raw palette (for marketing surfaces) -----
        'verde-paramo': palette.verdeParamo,
        'terracotta-inti': palette.terracottaInti,
        'amarillo-sol': palette.amarilloSol,
        algodon: palette.algodon,
        tierra: palette.tierra,
        niebla: palette.niebla,
        piedra: palette.piedra,
        'success-eco': palette.successEco,

        // ----- Semantic (light/dark via CSS variables) -----
        background: cssVar('background'),
        surface: cssVar('surface'),
        'surface-muted': cssVar('surface-muted'),
        overlay: cssVar('overlay'),

        border: cssVar('border'),
        'border-strong': cssVar('border-strong'),

        foreground: cssVar('text'),
        muted: cssVar('text-muted'),
        inverse: cssVar('text-inverse'),

        primary: {
          DEFAULT: cssVar('primary'),
          hover: cssVar('primary-hover'),
          active: cssVar('primary-active'),
          soft: cssVar('primary-soft'),
          foreground: cssVar('text-on-primary'),
        },
        secondary: {
          DEFAULT: cssVar('secondary'),
          hover: cssVar('secondary-hover'),
          soft: cssVar('secondary-soft'),
        },
        accent: {
          DEFAULT: cssVar('accent'),
          soft: cssVar('accent-soft'),
        },

        success: { DEFAULT: cssVar('success'), soft: cssVar('success-soft') },
        warning: { DEFAULT: cssVar('warning'), soft: cssVar('warning-soft') },
        destructive: { DEFAULT: cssVar('error'), soft: cssVar('error-soft') },
        info: { DEFAULT: cssVar('info'), soft: cssVar('info-soft') },

        ring: cssVar('focus-ring'),
      },

      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
        heading: ['var(--font-poppins)', 'Poppins', 'system-ui', 'sans-serif'],
        accent: ['var(--font-fraunces)', 'Fraunces', 'Georgia', 'serif'],
      },

      fontSize: {
        h1: [`${typeScale.h1.fontSize}px`, { lineHeight: `${typeScale.h1.lineHeight}px` }],
        h2: [`${typeScale.h2.fontSize}px`, { lineHeight: `${typeScale.h2.lineHeight}px` }],
        h3: [`${typeScale.h3.fontSize}px`, { lineHeight: `${typeScale.h3.lineHeight}px` }],
        body: [`${typeScale.body.fontSize}px`, { lineHeight: `${typeScale.body.lineHeight}px` }],
        small: [`${typeScale.small.fontSize}px`, { lineHeight: `${typeScale.small.lineHeight}px` }],
        caption: [
          `${typeScale.caption.fontSize}px`,
          { lineHeight: `${typeScale.caption.lineHeight}px` },
        ],
      },

      spacing: Object.fromEntries(
        Object.entries(spacing).map(([k, v]) => [k, `${v}px`]),
      ),

      borderRadius: {
        none: `${radii.none}px`,
        sm: `${radii.sm}px`,
        DEFAULT: `${radii.md}px`,
        md: `${radii.md}px`,
        lg: `${radii.lg}px`,
        xl: `${radii.xl}px`,
        full: `${radii.full}px`,
      },

      boxShadow: {
        sm: '0 1px 2px rgba(27, 45, 42, 0.08)',
        DEFAULT: '0 4px 12px rgba(27, 45, 42, 0.10)',
        md: '0 4px 12px rgba(27, 45, 42, 0.10)',
        lg: '0 12px 32px rgba(27, 45, 42, 0.14)',
      },
    },
  },
  plugins: [animate],
};

// Silence unused warning; helper kept for future opacity-aware migration.
void semantic;

export default config;
