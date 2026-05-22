export type BusinessType =
  | 'restaurant'
  | 'bakery'
  | 'supermarket'
  | 'hotel'
  | 'mercado'
  | 'farmer';

export type BusinessStatus = 'pending' | 'approved' | 'suspended' | 'rejected';

export interface Business {
  id: number;
  name: string;
  type: BusinessType;
  status: BusinessStatus;
  ruc?: string;
  description?: string;
  addressLine: string;
  city: string;
  province: string;
  latitude: number;
  longitude: number;
  logoUrl?: string;
  createdAt: string;
  updatedAt: string;
}
