'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
} from '@/components/ui';
import { createSalesDraft, sendSetupLink, type AdminBusinessDetail } from '@/lib/admin-api';

const schema = z.object({
  owner_email: z.string().email(),
  owner_phone: z.string().optional(),
  business_name: z.string().min(2),
  business_type: z.enum(['restaurant', 'bakery', 'supermarket', 'hotel', 'mercado', 'farmer']),
  tier: z.enum(['formal', 'informal']),
  description: z.string().optional(),
  location_name: z.string().optional(),
  address: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export default function NewBusinessBySalesPage() {
  const [created, setCreated] = useState<AdminBusinessDetail | null>(null);
  const [message, setMessage] = useState('');

  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { business_type: 'bakery', tier: 'formal' },
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Crear cuenta comercial</CardTitle>
          <CardDescription>
            Prefilla el negocio y luego envía el link para que configure su contraseña.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={handleSubmit(async (values) => {
              try {
                const business = await createSalesDraft(values);
                setCreated(business);
                setMessage('Cuenta creada. Ahora envía el link de configuración.');
              } catch (error) {
                setMessage(error instanceof Error ? error.message : 'No pudimos crear la cuenta.');
              }
            })}
          >
            <Field label="Email propietario" error={errors.owner_email?.message}>
              <Input
                type="email"
                {...register('owner_email')}
                error={Boolean(errors.owner_email)}
              />
            </Field>
            <Field label="Teléfono propietario" error={errors.owner_phone?.message}>
              <Input {...register('owner_phone')} />
            </Field>
            <Field label="Nombre negocio" error={errors.business_name?.message}>
              <Input {...register('business_name')} error={Boolean(errors.business_name)} />
            </Field>
            <Field label="Tipo negocio" error={errors.business_type?.message}>
              <select
                className="h-10 rounded-md border border-border bg-surface px-3 text-body"
                {...register('business_type')}
              >
                <option value="restaurant">Restaurant</option>
                <option value="bakery">Bakery</option>
                <option value="supermarket">Supermarket</option>
                <option value="hotel">Hotel</option>
                <option value="mercado">Mercado</option>
                <option value="farmer">Farmer</option>
              </select>
            </Field>
            <Field label="Tier" error={errors.tier?.message}>
              <select
                className="h-10 rounded-md border border-border bg-surface px-3 text-body"
                {...register('tier')}
              >
                <option value="formal">Formal</option>
                <option value="informal">Informal</option>
              </select>
            </Field>
            <Field label="Descripción" error={errors.description?.message}>
              <Input {...register('description')} />
            </Field>
            <Field label="Nombre ubicación" error={errors.location_name?.message}>
              <Input {...register('location_name')} />
            </Field>
            <Field label="Dirección" error={errors.address?.message}>
              <Input {...register('address')} />
            </Field>

            <div className="md:col-span-2 flex gap-3">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creando...' : 'Crear cuenta'}
              </Button>
              {created ? (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={async () => {
                    try {
                      const result = await sendSetupLink(created.id);
                      setMessage(`Link enviado a ${result.owner_email}.`);
                    } catch (error) {
                      setMessage(
                        error instanceof Error ? error.message : 'No pudimos enviar el link.',
                      );
                    }
                  }}
                >
                  Enviar link de contraseña
                </Button>
              ) : null}
            </div>
            {message ? <p className="md:col-span-2 text-small text-muted">{message}</p> : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="space-y-2 text-small text-muted">
      <span>{label}</span>
      {children}
      {error ? <p className="text-caption text-destructive">{error}</p> : null}
    </label>
  );
}
