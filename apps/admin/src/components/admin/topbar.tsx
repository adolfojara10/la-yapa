'use client';

import { usePathname } from 'next/navigation';

import { Avatar, AvatarFallback } from '@/components/ui';
import { useAdminAuthStore } from '@/lib/auth-store';

function breadcrumbLabel(segment: string): string {
  return segment.replace(/-/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function AdminTopbar() {
  const pathname = usePathname();
  const user = useAdminAuthStore((s) => s.user);
  const crumbs = pathname.split('/').filter(Boolean);

  return (
    <header className="flex items-center justify-between border-b border-border bg-background px-8 py-5">
      <div>
        <div className="flex items-center gap-2 text-caption uppercase tracking-[0.18em] text-muted">
          {crumbs.map((crumb, index) => (
            <span key={`${crumb}-${index}`}>
              {index > 0 ? ' / ' : ''}
              {breadcrumbLabel(crumb)}
            </span>
          ))}
        </div>
        <h2 className="mt-2 text-h2 text-foreground">
          {breadcrumbLabel(crumbs.at(-1) ?? 'dashboard')}
        </h2>
      </div>

      <div className="flex items-center gap-3">
        <Avatar>
          <AvatarFallback>{user?.email?.slice(0, 2).toUpperCase() ?? 'LY'}</AvatarFallback>
        </Avatar>
        <div className="text-right">
          <p className="text-small font-medium text-foreground">{user?.email}</p>
          <p className="text-caption uppercase tracking-[0.16em] text-muted">{user?.role}</p>
        </div>
      </div>
    </header>
  );
}
