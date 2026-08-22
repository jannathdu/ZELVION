import { requestWithAuth } from "./client";

export type DashboardData = {
  user: {
    id: string;
    email: string;
  };

  subscription: {
    plan_name: string | null;
    status: string | null;
    starts_at: string | null;
    ends_at: string | null;
  };

  usage: {
    used_bytes: number;
    limit_bytes: number | null;
    remaining_bytes: number | null;
  };

  devices: {
    total_devices: number;
    max_devices: number | null;
  };

  payments: {
    last_payment_status: string | null;
    last_payment_date: string | null;
  };
};


export function getDashboard(
  accessToken: string,
): Promise<DashboardData> {
  return requestWithAuth<DashboardData>(
    "/dashboard",
    accessToken,
  );
}