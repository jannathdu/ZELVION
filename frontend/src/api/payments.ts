import { requestWithAuth } from "./client";


export type PaymentOrder = {
  id: string;
  user_id: string;
  subscription_plan_id: string;
  provider: string;
  status: string;
  amount_minor_units: number;
  currency: string;
  created_at: string;
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