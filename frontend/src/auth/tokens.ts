import type { TokenResponse } from "../api/client";

const ACCESS_TOKEN_KEY = "zelvion_access_token";
const REFRESH_TOKEN_KEY = "zelvion_refresh_token";

export type StoredTokens = {
  accessToken: string;
  refreshToken: string;
};

export function saveTokens(tokens: TokenResponse): void {
  sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    tokens.access_token,
  );
  sessionStorage.setItem(
    REFRESH_TOKEN_KEY,
    tokens.refresh_token,
  );
}

export function getStoredTokens(): StoredTokens | null {
  const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);

  if (!accessToken || !refreshToken) {
    return null;
  }

  return {
    accessToken,
    refreshToken,
  };
}

export function clearTokens(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}