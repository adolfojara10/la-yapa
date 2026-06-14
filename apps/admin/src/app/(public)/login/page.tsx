'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
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
import { useAdminAuthStore } from '@/lib/auth-store';

const schema = z.object({
  email: z.string().email('Ingresa un email válido.'),
  password: z.string().min(8, 'Mínimo 8 caracteres.'),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const hydrate = useAdminAuthStore((s) => s.hydrate);
  const login = useAdminAuthStore((s) => s.login);
  const status = useAdminAuthStore((s) => s.status);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (status === 'authed') {
      router.replace('/dashboard');
    }
  }, [router, status]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Acceso del equipo</CardTitle>
          <CardDescription>Solo admins y reps de ventas pueden entrar aquí.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={handleSubmit(async (values) => {
              try {
                await login(values);
                router.replace('/dashboard');
              } catch (error) {
                setError('root', {
                  message: error instanceof Error ? error.message : 'No pudimos iniciar sesión.',
                });
              }
            })}
          >
            <div className="space-y-2">
              <label className="text-small text-muted">Email</label>
              <Input type="email" error={Boolean(errors.email)} {...register('email')} />
              {errors.email ? (
                <p className="text-caption text-destructive">{errors.email.message}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <label className="text-small text-muted">Contraseña</label>
              <Input type="password" error={Boolean(errors.password)} {...register('password')} />
              {errors.password ? (
                <p className="text-caption text-destructive">{errors.password.message}</p>
              ) : null}
            </div>
            {errors.root?.message ? (
              <p className="text-caption text-destructive">{errors.root.message}</p>
            ) : null}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
