# @layapa/ui

Single source of truth for La Yapa's design tokens.

> Brand reference: see `MASTER_VISION.md` → **Brand Identity**.

## What lives here

```
src/
├── tokens.ts   # palette, schemes (light/dark), type scale, spacing,
│               # radii, shadows, motion, zIndex, buildTheme(), cssVariables
└── index.ts    # re-exports tokens + back-compat aliases
```

There are **no React components in this package** — components live with their
host app (`apps/mobile/src/components/ui`, `apps/admin/src/components/ui`)
because RN and DOM components can't share implementation, only tokens.

---

## Tokens

### Colors

Two palettes are exported:

- **`palette`** — raw named brand colors (`palette.terracottaBrasa`, …). Use these
  only for marketing surfaces or one-off illustrations.
- **`lightScheme`, `darkScheme`** — _semantic_ tokens grouped by intent
  (`primary`, `surface`, `text`, `border`, `success`, …). Components should
  always consume these, never `palette.*` directly.

A helper `buildTheme(mode)` returns the full `Theme` object that the mobile
`ThemeProvider` injects via React context.

### Typography scale

Per master vision:

| Token        | Size / Line | Font / Weight |
| ------------ | ----------- | ------------- |
| `h1`         | 32 / 40     | Poppins 700   |
| `h2`         | 24 / 32     | Poppins 600   |
| `h3`         | 20 / 28     | Poppins 600   |
| `body`       | 16 / 24     | Inter 400     |
| `bodyStrong` | 16 / 24     | Inter 500     |
| `small`      | 14 / 20     | Inter 400     |
| `caption`    | 12 / 16     | Inter 500     |

### Spacing (4px base)

`0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16` → `0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64` px.

### Radii

`none(0) · sm(4) · md(8) · lg(12) · xl(16) · full(9999)`

### Shadows · Motion · Z-index

See `tokens.ts` for full structures. Shadows export both `.css` and `.rn`
shapes so the same token works in admin and mobile.

---

## How each app consumes tokens

### Admin (Next.js)

- `apps/admin/tailwind.config.ts` imports the palette + scale and wires
  semantic colors to CSS variables (`var(--color-primary)`, …).
- `apps/admin/src/app/globals.css` defines those variables for `:root` (light)
  and `.dark` (dark). Toggle the class on `<html>` (next-themes already
  handles this) to switch modes.
- Google fonts loaded once via `next/font` in `app/layout.tsx`; exposed as
  `font-sans`, `font-heading`, `font-accent` utilities.

```tsx
import { Button } from '@/components/ui';

<Button variant="primary">Confirmar</Button>;
```

### Mobile (Expo)

- `apps/mobile/src/theme/ThemeProvider.tsx` wraps the app and resolves
  `system | light | dark`. Use `useTheme()` to access the theme.
- Fonts loaded via `@expo-google-fonts/*` in `app/_layout.tsx`; the splash
  screen is held until they're ready.
- SVGs are imported as React components via `react-native-svg-transformer`
  (see `metro.config.js`).

```tsx
import { Button, Text } from '@/components/ui';
import { useTheme } from '@/theme';

function Example() {
  const { theme, toggle } = useTheme();
  return (
    <View style={{ padding: theme.spacing[4] }}>
      <Text variant="h2">Hola</Text>
      <Button onPress={toggle}>Cambiar tema</Button>
    </View>
  );
}
```

---

## Component inventory

### Mobile (`apps/mobile/src/components/ui/`)

| Component     | File              | Notes                                                         |
| ------------- | ----------------- | ------------------------------------------------------------- |
| `Text`        | `Text.tsx`        | Theme-aware text with variant + color tokens                  |
| `Button`      | `Button.tsx`      | primary / secondary / ghost / danger · sm / md / lg · loading |
| `Input`       | `Input.tsx`       | text / password / search · label · error / helper · icons     |
| `Card`        | `Card.tsx`        | Surface container with optional elevation                     |
| `Badge`       | `Badge.tsx`       | 7 tones, soft backgrounds                                     |
| `Avatar`      | `Avatar.tsx`      | Image with initials fallback, 4 sizes                         |
| `Modal`       | `Modal.tsx`       | Centered, animated, backdrop-dismissible                      |
| `BottomSheet` | `BottomSheet.tsx` | Wraps `@gorhom/bottom-sheet`, theme-styled handle/backdrop    |
| `Toast`       | `Toast.tsx`       | `ToastProvider` + `useToast({ title, tone, durationMs })`     |
| `Skeleton`    | `Skeleton.tsx`    | Pulse-animated placeholder                                    |
| `Icon`        | `Icon.tsx`        | Thin wrapper around `lucide-react-native` with theme tones    |

Showcase: run `pnpm --filter @layapa/mobile dev` → tap **Ver design system**.

### Admin (`apps/admin/src/components/ui/`)

| Component  | File           | Notes                                                      |
| ---------- | -------------- | ---------------------------------------------------------- |
| `Button`   | `button.tsx`   | shadcn-pattern (cva + Radix Slot) — 5 variants, 4 sizes    |
| `Input`    | `input.tsx`    | Includes `error` flag for invalid styling                  |
| `Card`     | `card.tsx`     | `Card · CardHeader · CardTitle · CardContent · CardFooter` |
| `Badge`    | `badge.tsx`    | 8 tone variants                                            |
| `Avatar`   | `avatar.tsx`   | Radix Avatar with brand fallback                           |
| `Dialog`   | `dialog.tsx`   | Radix Dialog, theme-styled                                 |
| `Toast`    | `toast.tsx`    | Radix Toast primitives — wire a `<ToastViewport>` once     |
| `Skeleton` | `skeleton.tsx` | Tailwind `animate-pulse`                                   |

Showcase: run `pnpm --filter @layapa/admin dev` → visit `http://localhost:3000`.

---

## Brand assets

Placeholder SVGs are committed and will be replaced once the illustrator
delivers final artwork.

- Mascot: `apps/mobile/src/assets/mascot/yapi-*.svg` (8 states)
- Logo: `apps/mobile/src/assets/logo/logo-*.svg` (4 variants, mirrored to
  `apps/admin/public/logo/`)

Use them via the brand components: `<Mascot state="happy" />` and `<Logo />`.

---

## Adding a token

1. Edit `packages/ui/src/tokens.ts`.
2. If it's a color: add it to both `lightScheme` and `darkScheme` (same key).
3. For admin: add the matching `--color-…` variable to `apps/admin/src/app/globals.css`
   in both `:root` and `.dark` blocks, then map it in `tailwind.config.ts`.
4. Mobile picks up the new token automatically via `buildTheme()`.
