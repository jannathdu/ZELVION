import { requestWithAuth } from "./client";


export type UsageRecord = {
  id: string;
  bytes_used: number;
  record_type: string;
  created_at: string;
};


export type UsageSummary = {
  used_bytes: number;
  limit_bytes: number | null;
  remaining_bytes: number | null;
};


export type CreateUsagePayload = {
  bytes_used: number;
  record_type?: string;
};


export function getUsageSummary(
  accessToken: string,
): Promise<UsageSummary> {
  return requestWithAuth<UsageSummary>(
    "/usage/summary",
    accessToken,
  );
}


export function createUsageRecord(
  accessToken: string,
  payload: CreateUsagePayload,
): Promise<UsageRecord> {
  return requestWithAuth<UsageRecord>(
    "/usage",
    accessToken,
    {
      method: "POST",
      body: JSON.stringify({
        bytes_used: payload.bytes_used,
        record_type:
          payload.record_type ?? "total",
      }),
    },
  );
}