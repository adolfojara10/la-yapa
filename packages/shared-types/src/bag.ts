export type BagKind = 'surprise' | 'specific';

export type BagCategory = 'bakery' | 'meal' | 'produce' | 'groceries' | 'mixed';

export interface Bag {
  id: number;
  businessId: number;
  kind: BagKind;
  category: BagCategory;
  title: string;
  description?: string;
  originalPrice: number;
  discountedPrice: number;
  quantityAvailable: number;
  pickupStart: string;
  pickupEnd: string;
  imageUrl?: string;
  createdAt: string;
  updatedAt: string;
}
