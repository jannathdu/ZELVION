const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type User = {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

type ApiErrorBody = {
  detail?: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getApiErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  return fallback;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  if (options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Request failed";

    try {
      const errorBody = (await response.json()) as ApiErrorBody;

      if (typeof errorBody.detail === "string") {
        message = errorBody.detail;
      }
    } catch {
      message = response.statusText || message;
    }

    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}


export function requestWithAuth<T>(
  path: string,
  accessToken: string,
  options: RequestInit = {},
): Promise<T> {
  return request<T>(path, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export function register(
  email: string,
  password: string,
): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function refresh(
  refreshToken: string,
): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function logout(refreshToken: string): Promise<void> {
  return request<void>("/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function getCurrentUser(
  accessToken: string,
): Promise<User> {
  return request<User>("/auth/me", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export type SubscriptionPlan = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  price_minor_units: number;
  currency: string;
  duration_days: number;
  data_limit_bytes: number | null;
  max_devices: number;
};

export function getSubscriptionPlans():
Promise<SubscriptionPlan[]> {
  return request<SubscriptionPlan[]>(
    "/subscriptions/plans",
  );
}