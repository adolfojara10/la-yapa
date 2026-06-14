'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BriefcaseBusiness, LayoutDashboard, LogOut, UserPlus } from 'lucide-react';

import { Button } from '@/components/ui';
import { useAdminAuthStore } from '@/lib/auth-store';
import { cn } from '@/lib/utils';

const ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/businesses/pending', label: 'Negocios', icon: BriefcaseBusiness },
  { href: '/sales-reps/new-business', label: 'Alta comercial', icon: UserPlus },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const logout = useAdminAuthStore((s) => s.logout);

  return (
    <aside className="flex min-h-screen w-72 flex-col border-r border-border bg-surface px-4 py-6">
      <div className="px-3">
        <p className="font-accent text-caption uppercase tracking-[0.2em] text-secondary">
          La Yapa
        </p>
        <h1 className="mt-2 text-h3 text-foreground">Panel operativo</h1>
      </div>

      <nav className="mt-8 flex flex-1 flex-col gap-1">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-small font-medium transition-colors',
                active
                  ? 'bg-primary-soft text-primary'
                  : 'text-muted hover:bg-surface-muted hover:text-foreground',
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <Button variant="ghost" className="justify-start" onClick={() => void logout()}>
        <LogOut className="h-4 w-4" />
        Cerrar sesión
      </Button>
    </aside>
  );
}
