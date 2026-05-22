'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

import {
  Avatar,
  AvatarFallback,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Input,
  Skeleton,
} from '@/components/ui';

export default function DesignSystemPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <main className="mx-auto max-w-5xl space-y-12 p-8">
      <header className="flex items-start justify-between">
        <div>
          <p className="font-accent text-small uppercase tracking-widest text-secondary">
            Design System
          </p>
          <h1 className="text-h1 text-foreground">La Yapa Admin</h1>
          <p className="mt-2 text-body text-muted">Comida rescatada, planeta cuidado.</p>
        </div>
        {mounted && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          >
            {theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
          </Button>
        )}
      </header>

      <section className="space-y-3">
        <h2 className="text-h2">Typography</h2>
        <p className="text-h1">H1 / 32 · Poppins Bold</p>
        <p className="text-h2">H2 / 24 · Poppins Semibold</p>
        <p className="text-h3">H3 / 20 · Poppins Semibold</p>
        <p className="text-body">Body / 16 · Inter Regular</p>
        <p className="text-small text-muted">Small / 14 · Inter Regular</p>
        <p className="text-caption uppercase tracking-wider text-muted">
          Caption / 12 · Inter Medium
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-h2">Colors</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ['background', 'bg-background border border-border'],
            ['surface', 'bg-surface border border-border'],
            ['primary', 'bg-primary text-primary-foreground'],
            ['secondary', 'bg-secondary text-inverse'],
            ['accent', 'bg-accent text-tierra'],
            ['success', 'bg-success text-inverse'],
            ['warning', 'bg-warning text-inverse'],
            ['destructive', 'bg-destructive text-inverse'],
          ].map(([name, cls]) => (
            <div key={name} className={`rounded-md p-4 ${cls}`}>
              <p className="text-small font-medium">{name}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-h2">Buttons</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="outline">Outline</Button>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
          <Button disabled>Disabled</Button>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-h2">Inputs</h2>
        <div className="grid max-w-md gap-3">
          <Input placeholder="Tu correo" type="email" />
          <Input placeholder="Contraseña" type="password" />
          <Input placeholder="Buscar negocios..." type="search" />
          <Input placeholder="Con error" error defaultValue="invalid@" />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-h2">Badges</h2>
        <div className="flex flex-wrap gap-2">
          <Badge>Default</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="accent">Accent</Badge>
          <Badge variant="success">Aprobado</Badge>
          <Badge variant="warning">Pendiente</Badge>
          <Badge variant="destructive">Rechazado</Badge>
          <Badge variant="info">Info</Badge>
          <Badge variant="outline">Outline</Badge>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-h2">Avatar · Card · Dialog · Skeleton</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarFallback>YP</AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle>Yapi Panadería</CardTitle>
                  <CardDescription>Cuenca · Bakery</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-small text-muted">
                Negocio de prueba. Bolsas sorpresa disponibles a partir de las 17:00.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Skeleton loader</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-24 w-full" />
            </CardContent>
          </Card>
        </div>

        <Dialog>
          <DialogTrigger asChild>
            <Button variant="secondary">Abrir diálogo</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>¿Confirmar acción?</DialogTitle>
              <DialogDescription>
                Esto aprobará al negocio y enviará un correo de bienvenida.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="ghost">Cancelar</Button>
              <Button variant="primary">Aprobar</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </section>
    </main>
  );
}
