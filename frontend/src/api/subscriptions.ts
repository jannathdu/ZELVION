import { requestWithAuth } from "./client";


export type UserSubscription = {
  id: string;
  plan_id: string;
  status: "active" | "expired" | "cancelled";
  price_minor_units: number;
  currency: string;
  duration_days: number;
  data_limit_bytes: number | null;
  max_devices: number;
  starts_at: string;
  ends_at: string;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
};


export function getMySubscription(
  accessToken: string,
): Promise<UserSubscription | null> {
  return requestWithAuth<UserSubscription | null>(
    "/subscriptions/me",
    accessToken,
  );
}


export function renewMySubscription(
  accessToken: string,
): Promise<UserSubscription> {
  return requestWithAuth<UserSubscription>(
    "/subscriptions/mock-renew",
    accessToken,
    {
      method: "POST",
    },
  );
}