import { Badge } from '@/components/ui';

export function BusinessStatusBadge({ status }: { status: string }) {
  const variant =
    status === 'approved'
      ? 'success'
      : status === 'rejected'
        ? 'destructive'
        : status === 'suspended'
          ? 'secondary'
          : 'warning';

  return <Badge variant={variant}>{status}</Badge>;
}
