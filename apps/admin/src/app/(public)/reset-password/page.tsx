'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
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
import { resetPassword } from '@/lib/admin-api';

const schema = z
  .object({
    password: z.string().min(8, 'Mínimo 8 caracteres.'),
    confirm: z.string().min(8, 'Confirma tu contraseña.'),
  })
  .refine((data) => data.password === data.confirm, {
    path: ['confirm'],
    message: 'Las contraseñas deben coincidir.',
  });

type FormValues = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const token = params.get('token') ?? '';
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Configura tu contraseña</CardTitle>
          <CardDescription>
            Este link es de un solo uso. Crea tu nueva contraseña para entrar al panel y la app de
            negocios.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={handleSubmit(async (values) => {
              try {
                await resetPassword({ token, new_password: values.password });
                setError('root', { message: 'Contraseña guardada. Ya puedes iniciar sesión.' });
              } catch (error) {
                setError('root', {
                  message:
                    error instanceof Error ? error.message : 'No pudimos guardar tu contraseña.',
                });
              }
            })}
          >
            <div className="space-y-2">
              <label className="text-small text-muted">Nueva contraseña</label>
              <Input type="password" error={Boolean(errors.password)} {...register('password')} />
              {errors.password ? (
                <p className="text-caption text-destructive">{errors.password.message}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <label className="text-small text-muted">Confirmar contraseña</label>
              <Input type="password" error={Boolean(errors.confirm)} {...register('confirm')} />
              {errors.confirm ? (
                <p className="text-caption text-destructive">{errors.confirm.message}</p>
              ) : null}
            </div>
            {errors.root?.message ? (
              <p className="text-caption text-muted">{errors.root.message}</p>
            ) : null}
            <Button type="submit" className="w-full" disabled={isSubmitting || !token}>
              {isSubmitting ? 'Guardando...' : 'Guardar contraseña'}
            </Button>
            <p className="text-center text-small text-muted">
              <Link href="/login" className="text-primary underline-offset-2 hover:underline">
                Volver a login
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
