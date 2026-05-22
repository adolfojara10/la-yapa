export type OrderStatus =
  | 'pending_payment'
  | 'paid'
  | 'ready_for_pickup'
  | 'completed'
  | 'cancelled'
  | 'refunded';

export type PaymentMethod = 'payphone' | 'deuna' | 'kushki' | 'cash';

export interface Order {
  id: number;
  consumerId: number;
  bagId: number;
  status: OrderStatus;
  totalAmount: number;
  paymentMethod: PaymentMethod;
  pickupCode: string;
  createdAt: string;
  updatedAt: string;
}
