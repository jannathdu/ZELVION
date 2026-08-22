import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  createDevice,
  getDevices,
  revokeDevice,
  type Device,
} from "../api/devices";

import {
  getDashboard,
  type DashboardData,
} from "../api/dashboard";

import { getStoredTokens } from "../auth/tokens";
import { useAuth } from "../auth/AuthContext";


async function generateDeviceKeyHash(
  name: string,
  platform: string,
): Promise<string> {
  const source = [
    name,
    platform,
    crypto.randomUUID(),
    Date.now().toString(),
  ].join("|");

  const encoded = new TextEncoder().encode(source);

  const digest = await crypto.subtle.digest(
    "SHA-256",
    encoded,
  );

  return Array.from(
    new Uint8Array(digest),
  )
    .map((byte) =>
      byte.toString(16).padStart(2, "0"),
    )
    .join("");
}


export function DevicesPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const [devices, setDevices] =
    useState<Device[]>([]);

  const [dashboard, setDashboard] =
    useState<DashboardData | null>(null);

  const [name, setName] =
    useState("");

  const [platform, setPlatform] =
    useState("windows");

  const [error, setError] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(true);

  const [isRegistering, setIsRegistering] =
    useState(false);

  const [revokingDeviceId, setRevokingDeviceId] =
    useState<string | null>(null);

  const [isSigningOut, setIsSigningOut] =
    useState(false);


  async function refreshData(): Promise<void> {
    const tokens = getStoredTokens();

    if (!tokens) {
      return;
    }

    const [
      deviceData,
      dashboardData,
    ] = await Promise.all([
      getDevices(tokens.accessToken),
      getDashboard(tokens.accessToken),
    ]);

    setDevices(deviceData);
    setDashboard(dashboardData);
  }


  useEffect(() => {
    async function loadData() {
      try {
        await refreshData();
      } catch {
        setError(
          "Unable to load device information.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadData();
  }, []);


  async function handleRegisterDevice(
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    const trimmedName = name.trim();

    if (!trimmedName) {
      setError(
        "Please enter a device name.",
      );
      return;
    }

    const tokens = getStoredTokens();

    if (!tokens) {
      return;
    }

    setIsRegistering(true);
    setError("");

    try {
      const deviceKeyHash =
        await generateDeviceKeyHash(
          trimmedName,
          platform,
        );

      await createDevice(
        tokens.accessToken,
        {
          device_key_hash: deviceKeyHash,
          name: trimmedName,
          platform,
        },
      );

      setName("");

      await refreshData();

    } catch {
      setError(
        "Device registration failed. Check your subscription or device limit.",
      );
    } finally {
      setIsRegistering(false);
    }
  }


  async function handleRevokeDevice(
    deviceId: string,
  ): Promise<void> {
    const tokens = getStoredTokens();

    if (!tokens) {
      return;
    }

    setRevokingDeviceId(deviceId);
    setError("");

    try {
      await revokeDevice(
        tokens.accessToken,
        deviceId,
      );

      await refreshData();

    } catch {
      setError(
        "Unable to revoke this device.",
      );
    } finally {
      setRevokingDeviceId(null);
    }
  }


  async function handleSignOut(): Promise<void> {
    setIsSigningOut(true);

    await signOut();

    navigate(
      "/login",
      {
        replace: true,
      },
    );
  }


  const activeDevices =
    devices.filter(
      (device) => device.is_active,
    );

  const maxDevices =
    dashboard?.devices.max_devices ?? null;

  const hasActiveSubscription =
    dashboard?.subscription.status === "active";

  const deviceLimitReached =
    maxDevices !== null &&
    activeDevices.length >= maxDevices;


  return (
    <div className="dashboard-shell">

      <aside className="sidebar">

        <div>

          <div className="brand dashboard-brand">
            <span className="brand-mark">
              Z
            </span>

            <span>
              ZELVION
            </span>
          </div>


          <nav className="sidebar-nav">

            <Link
              className="nav-item"
              to="/dashboard"
            >
              Overview
            </Link>

            <Link
              className="nav-item active"
              to="/devices"
            >
              Devices
            </Link>

            <a className="nav-item">
              Subscription
            </a>

            <a className="nav-item">
              Usage
            </a>

          </nav>

        </div>


        <div className="sidebar-footer">

          <span className="sidebar-label">
            Signed in as
          </span>

          <strong>
            {user?.email}
          </strong>

          <button
            className="text-button"
            type="button"
            disabled={isSigningOut}
            onClick={() =>
              void handleSignOut()
            }
          >
            {
              isSigningOut
                ? "Signing out..."
                : "Sign out"
            }
          </button>

        </div>

      </aside>


      <main className="dashboard-main">

        <header className="dashboard-header">

          <div>

            <span className="eyebrow">
              Device management
            </span>

            <h1>
              Your devices
            </h1>

            <p>
              Register and revoke devices
              connected to your ZELVION account.
            </p>

          </div>

        </header>


        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        <section className="status-grid">

          <article className="status-card">

            <div className="card-label">
              Active Devices
            </div>

            <strong className="card-value">
              {
                isLoading
                  ? "Loading..."
                  : `${activeDevices.length}/${maxDevices ?? "∞"}`
              }
            </strong>

            <p>
              Current device usage
            </p>

          </article>


          <article className="status-card">

            <div className="card-label">
              Subscription
            </div>

            <strong className="card-value">
              {
                dashboard
                  ?.subscription
                  .plan_name
                  ?? "No Plan"
              }
            </strong>

            <p>
              Status:{" "}
              {
                dashboard
                  ?.subscription
                  .status
                  ?? "Inactive"
              }
            </p>

          </article>

        </section>


        <section className="account-section">

          <h2>
            Register a device
          </h2>

          {
            !hasActiveSubscription ? (
              <p className="error-message">
                An active subscription is required
                before registering devices.
              </p>
            ) : deviceLimitReached ? (
              <p className="error-message">
                Your device limit has been reached.
                Revoke a device before adding another.
              </p>
            ) : (
              <form
                onSubmit={(event) =>
                  void handleRegisterDevice(event)
                }
              >

                <label>
                  Device name
                </label>

                <input
                  type="text"
                  value={name}
                  placeholder="Example: My Laptop"
                  maxLength={100}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                />


                <label>
                  Platform
                </label>

                <select
                  value={platform}
                  onChange={(event) =>
                    setPlatform(
                      event.target.value,
                    )
                  }
                >
                  <option value="windows">
                    Windows
                  </option>

                  <option value="macos">
                    macOS
                  </option>

                  <option value="linux">
                    Linux
                  </option>

                  <option value="android">
                    Android
                  </option>

                  <option value="ios">
                    iOS
                  </option>
                </select>


                <button
                  className="plan-button"
                  type="submit"
                  disabled={isRegistering}
                >
                  {
                    isRegistering
                      ? "Registering..."
                      : "Register Device"
                  }
                </button>

              </form>
            )
          }

        </section>


        <section className="plans-section">

          <div className="section-heading">

            <span className="eyebrow">
              Registered devices
            </span>

            <h2>
              Device list
            </h2>

          </div>


          {
            isLoading ? (
              <p>
                Loading devices...
              </p>
            ) : devices.length === 0 ? (
              <p>
                No devices registered yet.
              </p>
            ) : (
              <div className="plans-grid">

                {
                  devices.map((device) => (

                    <article
                      className="plan-card"
                      key={device.id}
                    >

                      <h3>
                        {device.name}
                      </h3>

                      <p>
                        Platform:{" "}
                        <strong>
                          {device.platform}
                        </strong>
                      </p>

                      <p>
                        Status:{" "}
                        <strong>
                          {
                            device.is_active
                              ? "Active"
                              : "Revoked"
                          }
                        </strong>
                      </p>

                      <p>
                        Added:{" "}
                        {
                          new Date(
                            device.created_at,
                          ).toLocaleString()
                        }
                      </p>


                      {
                        device.is_active && (
                          <button
                            className="plan-button"
                            type="button"
                            disabled={
                              revokingDeviceId
                              === device.id
                            }
                            onClick={() =>
                              void handleRevokeDevice(
                                device.id,
                              )
                            }
                          >
                            {
                              revokingDeviceId
                              === device.id
                                ? "Revoking..."
                                : "Revoke Device"
                            }
                          </button>
                        )
                      }

                    </article>

                  ))
                }

              </div>
            )
          }

        </section>

      </main>

    </div>
  );
}