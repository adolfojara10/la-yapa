import type { LatLng, Locale, User, UserRole } from './user';

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface RegisterPayload {
  email: string;
  password: string;
  role?: Extract<UserRole, 'consumer' | 'business_owner'>;
  first_name?: string;
  last_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface GoogleLoginPayload {
  id_token: string;
}

export interface AppleLoginPayload {
  identity_token: string;
  first_name?: string;
  last_name?: string;
}

export interface VerifyEmailPayload {
  email: string;
  code: string;
}

export interface ResendVerificationPayload {
  email: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export interface LogoutPayload {
  refresh: string;
}

export interface UpdateMePayload {
  language?: Locale;
  phone?: string;
  first_name?: string;
  last_name?: string;
  default_address?: string;
  default_location?: LatLng | null;
  dietary_preferences?: string[];
  avatar_url?: string;
}
