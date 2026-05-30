'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';
import type { ThemeProviderProps } from 'next-themes/dist/types';

// Import the props type directly instead of inferring via
// `ComponentProps<typeof NextThemesProvider>`. The component's declared return
// type in next-themes' .d.ts is `string | number | boolean | Iterable<…> |
// JSX.Element`, which is invalid for a JSX component under React 19's stricter
// `ReactNode` typing (which now includes `bigint`). The mismatch surfaces as
// "Property 'children' does not exist on type 'IntrinsicAttributes'" when
// admin (React 18) and mobile (React 19) coexist in the workspace.
export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
