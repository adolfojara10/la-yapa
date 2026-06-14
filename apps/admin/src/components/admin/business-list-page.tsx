'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { BusinessStatusBadge } from '@/components/admin/business-status-badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { fetchBusinesses } from '@/lib/admin-api';

export function BusinessListPage({ status }: { status: 'pending' | 'approved' | 'suspended' }) {
  const query = useQuery({
    queryKey: ['admin-businesses', status],
    queryFn: () => fetchBusinesses(status),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Negocios {status}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {query.data?.map((business) => (
          <Link
            key={business.id}
            href={`/businesses/${business.id}`}
            className="flex items-center justify-between rounded-md border border-border px-4 py-3 transition-colors hover:bg-surface-muted"
          >
            <div>
              <p className="text-body font-medium text-foreground">{business.name}</p>
              <p className="text-small text-muted">
                {business.owner_email} · {business.business_type}
              </p>
            </div>
            <BusinessStatusBadge status={business.status} />
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
