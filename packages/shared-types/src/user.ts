export type UserRole = 'consumer' | 'business' | 'admin';

export type Locale = 'es' | 'en';

export interface User {
  id: number;
  email: string;
  username: string;
  role: UserRole;
  phone?: string;
  locale: Locale;
  createdAt: string;
  updatedAt: string;
}
