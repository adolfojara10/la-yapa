import type { BusinessSummary } from './business';

export type UserRole = 'consumer' | 'business_owner' | 'admin' | 'sales_rep';

export type Locale = 'es' | 'en';

export interface LatLng {
  lat: number;
  lng: number;
}

export interface ConsumerProfile {
  first_name: string;
  last_name: string;
  avatar_url?: string;
  default_location?: LatLng | null;
  default_address?: string;
  dietary_preferences: string[];
  referral_code: string;
  onboarding_completed: boolean;
}

export interface User {
  id: number;
  email: string;
  role: UserRole;
  language: Locale;
  phone?: string;
  is_email_verified: boolean;
  email_verified_at?: string | null;
  is_premium: boolean;
  premium_expires_at?: string | null;
  consumer_profile?: ConsumerProfile | null;
  business_summary?: BusinessSummary | null;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}
