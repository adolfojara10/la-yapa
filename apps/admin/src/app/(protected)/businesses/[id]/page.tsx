'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';

import { BusinessStatusBadge } from '@/components/admin/business-status-badge';
import { DocumentPreview } from '@/components/admin/document-preview';
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui';
import { approveBusiness, fetchBusiness, rejectBusiness, requestMoreInfo } from '@/lib/admin-api';

export default function BusinessDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [reason, setReason] = useState('');
  const [mode, setMode] = useState<'reject' | 'more-info' | null>(null);
  const id = Number(Array.isArray(params.id) ? params.id[0] : params.id);

  const query = useQuery({ queryKey: ['admin-business', id], queryFn: () => fetchBusiness(id) });

  const approve = useMutation({
    mutationFn: () => approveBusiness(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin-business', id] });
      await queryClient.invalidateQueries({ queryKey: ['admin-businesses'] });
    },
  });

  const reject = useMutation({
    mutationFn: (message: string) => rejectBusiness(id, message),
    onSuccess: async () => {
      setReason('');
      setMode(null);
      await queryClient.invalidateQueries({ queryKey: ['admin-business', id] });
      await queryClient.invalidateQueries({ queryKey: ['admin-businesses'] });
    },
  });

  const moreInfo = useMutation({
    mutationFn: (message: string) => requestMoreInfo(id, message),
    onSuccess: async () => {
      setReason('');
      setMode(null);
      await queryClient.invalidateQueries({ queryKey: ['admin-business', id] });
      await queryClient.invalidateQueries({ queryKey: ['admin-businesses'] });
    },
  });

  const business = query.data;
  if (!business) {
    return <div>Cargando negocio...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-h1 text-foreground">{business.name}</h1>
          <p className="mt-2 text-body text-muted">
            {business.owner_email} · {business.business_type} · {business.tier}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <BusinessStatusBadge status={business.status} />
          <Button variant="ghost" onClick={() => router.push(`/businesses/${business.status}`)}>
            Volver a la cola
          </Button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Información del negocio</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-small text-foreground">
            <p>
              <strong>Descripción:</strong> {business.description || 'Sin descripción'}
            </p>
            <p>
              <strong>Teléfono:</strong> {business.phone || 'Sin teléfono'}
            </p>
            <p>
              <strong>Email:</strong> {business.email || 'Sin email comercial'}
            </p>
            <p>
              <strong>Website:</strong> {business.website || 'Sin website'}
            </p>
            <p>
              <strong>Payout:</strong> {business.payout_method} · {business.payout_frequency}
            </p>
            <p>
              <strong>Notas revisión:</strong> {business.review_notes || 'Ninguna'}
            </p>
            <p>
              <strong>Motivo rechazo:</strong> {business.rejection_reason || 'Ninguno'}
            </p>

            <div className="space-y-2">
              <h3 className="text-body font-semibold">Ubicaciones</h3>
              {business.locations.map((location) => (
                <div key={location.id} className="rounded-md border border-border p-3">
                  <p className="font-medium">{location.name}</p>
                  <p className="text-muted">{location.address}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Acciones</CardTitle>
            <CardDescription>Aprueba, rechaza o solicita más información.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full"
              onClick={() => approve.mutate()}
              disabled={approve.isPending}
            >
              {approve.isPending ? 'Aprobando...' : 'Aprobar negocio'}
            </Button>
            <Button className="w-full" variant="outline" onClick={() => setMode('more-info')}>
              Solicitar más información
            </Button>
            <Button className="w-full" variant="danger" onClick={() => setMode('reject')}>
              Rechazar
            </Button>

            {mode ? (
              <div className="space-y-3 rounded-md border border-border bg-background p-3">
                <label className="text-small text-muted">
                  {mode === 'reject' ? 'Motivo del rechazo' : 'Notas para el negocio'}
                </label>
                <textarea
                  className="min-h-28 w-full rounded-md border border-border bg-surface px-3 py-2 text-small text-foreground"
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
                <div className="flex gap-2">
                  <Button
                    variant={mode === 'reject' ? 'danger' : 'secondary'}
                    onClick={() =>
                      mode === 'reject'
                        ? reject.mutate(reason.trim())
                        : moreInfo.mutate(reason.trim())
                    }
                    disabled={reject.isPending || moreInfo.isPending || !reason.trim()}
                  >
                    Enviar
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setMode(null);
                      setReason('');
                    }}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Documentos</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <DocumentSlot label="RUC" url={business.verification?.ruc_document_url ?? ''} />
          <DocumentSlot label="Cédula" url={business.verification?.cedula_document_url ?? ''} />
          <DocumentSlot
            label="Permiso de funcionamiento"
            url={business.verification?.permiso_funcionamiento_url ?? ''}
          />
          <DocumentSlot label="ARCSA" url={business.verification?.arcsa_url ?? ''} />
          <DocumentSlot
            label="Comprobante bancario"
            url={business.verification?.bank_proof_url ?? ''}
          />
          <DocumentSlot
            label="Foto negocio"
            url={business.verification?.business_photo_url ?? ''}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function DocumentSlot({ label, url }: { label: string; url: string }) {
  return (
    <div className="space-y-2">
      <p className="text-small font-medium text-foreground">{label}</p>
      <DocumentPreview url={url} />
    </div>
  );
}
