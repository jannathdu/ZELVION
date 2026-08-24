import { requestWithAuth } from "./client";


export type PaymentOrder = {
  id: string;
  subscription_plan_id: string;
  amount: number;
  currency: string;
  provider: string;
  provider_transaction_id: string | null;
  status: string;
  created_at: string;
  paid_at: string | null;
};


export type PaymentHistoryResponse = {
  payments: PaymentOrder[];
};


export type AlipayOrderResponse = {
  payment_id: string;
  payment_url: string;
};


export function createPaymentOrder(
  accessToken: string,
  subscriptionPlanId: string,
): Promise<PaymentOrder> {
  return requestWithAuth<PaymentOrder>(
    "/payments/create",
    accessToken,
    {
      method: "POST",
      body: JSON.stringify({
        subscription_plan_id: subscriptionPlanId,
        provider: "alipay",
      }),
    },
  );
}


export function createAlipayOrder(
  accessToken: string,
  paymentId: string,
): Promise<AlipayOrderResponse> {
  return requestWithAuth<AlipayOrderResponse>(
    `/payments/${paymentId}/alipay-order`,
    accessToken,
    {
      method: "POST",
    },
  );
}


export function completePayment(
  accessToken: string,
  paymentId: string,
): Promise<PaymentOrder> {
  return requestWithAuth<PaymentOrder>(
    `/payments/${paymentId}/success`,
    accessToken,
    {
      method: "POST",
      body: JSON.stringify({
        provider_transaction_id:
          `demo-${Date.now()}`,
      }),
    },
  );
}


export function getPaymentHistory(
  accessToken: string,
): Promise<PaymentHistoryResponse> {
  return requestWithAuth<PaymentHistoryResponse>(
    "/payments/history",
    accessToken,
  );
}