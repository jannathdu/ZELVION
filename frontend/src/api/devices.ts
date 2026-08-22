import { requestWithAuth } from "./client";

export type Device = {
  id: string;
  device_key_hash: string;
  name: string;
  platform: string;
  is_active: boolean;
  last_seen_at: string | null;
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateDevicePayload = {
  device_key_hash: string;
  name: string;
  platform: string;
};

export function getDevices(
  accessToken: string,
): Promise<Device[]> {
  return requestWithAuth<Device[]>(
    "/devices",
    accessToken,
  );
}

export function createDevice(
  accessToken: string,
  payload: CreateDevicePayload,
): Promise<Device> {
  return requestWithAuth<Device>(
    "/devices",
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function revokeDevice(
  accessToken: string,
  deviceId: string,
): Promise<Device> {
  return requestWithAuth<Device>(
    `/devices/${deviceId}`,
    accessToken,
    {
      method: "DELETE",
    },
  );
}