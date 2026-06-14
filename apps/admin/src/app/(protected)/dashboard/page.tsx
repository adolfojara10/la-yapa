'use client';

import { useQuery } from '@tanstack/react-query';

import { BusinessStatusBadge } from '@/components/admin/business-status-badge';
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui';
import { fetchBusinesses } from '@/lib/admin-api';

export default function DashboardPage() {
  const pending = useQuery({
    queryKey: ['admin-businesses', 'pending'],
    queryFn: () => fetchBusinesses('pending'),
  });
  const approved = useQuery({
    queryKey: ['admin-businesses', 'approved'],
    queryFn: () => fetchBusinesses('approved'),
  });
  const suspended = useQuery({
    queryKey: ['admin-businesses', 'suspended'],
    queryFn: () => fetchBusinesses('suspended'),
  });

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Pendientes" value={pending.data?.length ?? 0} />
        <MetricCard label="Aprobados" value={approved.data?.length ?? 0} />
        <MetricCard label="Suspendidos" value={suspended.data?.length ?? 0} />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Negocios esperando revisión</CardTitle>
          <CardDescription>La cola operativa más urgente del día.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {pending.data?.slice(0, 5).map((business) => (
            <div
              key={business.id}
              className="flex items-center justify-between rounded-md border border-border px-4 py-3"
            >
              <div>
                <p className="text-body font-medium text-foreground">{business.name}</p>
                <p className="text-small text-muted">{business.owner_email}</p>
              </div>
              <div className="flex items-center gap-3">
                <BusinessStatusBadge status={business.status} />
                <Button asChild variant="ghost">
                  <a href={`/businesses/${business.id}`}>Abrir</a>
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle>{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}
