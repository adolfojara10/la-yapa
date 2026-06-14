'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { AdminSidebar } from '@/components/admin/sidebar';
import { AdminTopbar } from '@/components/admin/topbar';
import { useAdminAuthStore } from '@/lib/auth-store';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const status = useAdminAuthStore((s) => s.status);
  const hydrate = useAdminAuthStore((s) => s.hydrate);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (status === 'idle') {
      router.replace('/login');
    }
  }, [router, status]);

  if (status !== 'authed') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">Cargando…</main>
    );
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <AdminSidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <AdminTopbar />
        <main className="flex-1 px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
