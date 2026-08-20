import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getSubscriptionPlans,
  type SubscriptionPlan,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";


function formatPrice(plan: SubscriptionPlan): string {
  const amount = plan.price_minor_units / 100;

  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: plan.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDataLimit(bytes: number | null): string {
  if (bytes === null) {
    return "Unlimited data";
  }

  const gibibytes = bytes / 1024 ** 3;
  return `${gibibytes.toFixed(0)} GB data`;
}

export function DashboardPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const [isSigningOut, setIsSigningOut] = useState(false);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [plansError, setPlansError] = useState("");
  const [arePlansLoading, setArePlansLoading] =
    useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadPlans(): Promise<void> {
      try {
        const availablePlans =
          await getSubscriptionPlans();

        if (isActive) {
          setPlans(availablePlans);
        }
      } catch {
        if (isActive) {
          setPlansError(
            "Plans are temporarily unavailable.",
          );
        }
      } finally {
        if (isActive) {
          setArePlansLoading(false);
        }
      }
    }

    void loadPlans();

    return () => {
      isActive = false;
    };
  }, []);

  async function handleSignOut(): Promise<void> {
    setIsSigningOut(true);
    await signOut();

    navigate("/login", {
      replace: true,
      state: {
        message: "You have been signed out securely.",
      },
    });
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div>
          <div className="brand dashboard-brand">
            <span className="brand-mark">Z</span>
            <span>ZELVION</span>
          </div>

          <nav className="sidebar-nav" aria-label="Dashboard">
            <a className="nav-item active" href="#overview">
              <span>Overview</span>
            </a>
            <a className="nav-item" href="#devices">
              <span>Devices</span>
            </a>
            <a className="nav-item" href="#subscription">
              <span>Subscription</span>
            </a>
            <a className="nav-item" href="#usage">
              <span>Usage</span>
            </a>
          </nav>
        </div>

        <div className="sidebar-footer">
          <span className="sidebar-label">Signed in as</span>
          <strong>{user?.email}</strong>
          <button
            className="text-button"
            type="button"
            onClick={() => void handleSignOut()}
            disabled={isSigningOut}
          >
            {isSigningOut ? "Signing out..." : "Sign out"}
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <span className="eyebrow">Account overview</span>
            <h1>Welcome to ZELVION</h1>
            <p>
              Manage your account, subscription, devices,
              and protected connections.
            </p>
          </div>

          <div className="account-badge">
            <span className="status-dot" />
            Account active
          </div>
        </header>

        <section className="status-grid" id="overview">
          <article className="status-card featured">
            <div className="card-label">Protection status</div>
            <div className="protection-state">
              <span className="shield-icon">Z</span>
              <div>
                <strong>Not connected</strong>
                <p>
                  Secure network service is not configured yet.
                </p>
              </div>
            </div>
            <button
              className="secondary-button"
              type="button"
              disabled
            >
              Connect unavailable
            </button>
          </article>

          <article className="status-card">
            <div className="card-label">Subscription</div>
            <strong className="card-value">
              No active plan
            </strong>
            <p>
              Choose a plan below to prepare your account.
            </p>
          </article>

          <article className="status-card" id="devices">
            <div className="card-label">
              Registered devices
            </div>
            <strong className="card-value">0 / 3</strong>
            <p>
              Device management has not been enabled yet.
            </p>
          </article>

          <article className="status-card" id="usage">
            <div className="card-label">Traffic usage</div>
            <strong className="card-value">0 GB</strong>
            <p>
              Usage tracking begins after service activation.
            </p>
          </article>
        </section>

        <section
          className="plans-section"
          id="subscription"
        >
          <div className="section-heading plans-heading">
            <div>
              <span className="eyebrow">Plans</span>
              <h2>Choose your access period</h2>
              <p>
                Simple CNY pricing with clear data and
                device limits.
              </p>
            </div>
          </div>

          {arePlansLoading && (
            <p className="plans-message">
              Loading available plans...
            </p>
          )}

          {plansError && (
            <div className="error-message" role="alert">
              {plansError}
            </div>
          )}

          {!arePlansLoading && !plansError && (
            <div className="plans-grid">
              {plans.map((plan) => (
                <article className="plan-card" key={plan.id}>
                  <div>
                    <span className="plan-code">
                      {plan.duration_days === 1
                        ? "Flexible access"
                        : "Best monthly value"}
                    </span>
                    <h3>{plan.name}</h3>
                    <div className="plan-price">
                      {formatPrice(plan)}
                    </div>
                    <p className="plan-description">
                      {plan.description}
                    </p>
                  </div>

                  <ul className="plan-features">
                    <li>
                      {plan.duration_days}{" "}
                      {plan.duration_days === 1
                        ? "day"
                        : "days"}{" "}
                      of access
                    </li>
                    <li>
                      {formatDataLimit(
                        plan.data_limit_bytes,
                      )}
                    </li>
                    <li>
                      Up to {plan.max_devices}{" "}
                      {plan.max_devices === 1
                        ? "device"
                        : "devices"}
                    </li>
                    <li>Secure account authentication</li>
                  </ul>

                  <button
                    className="plan-button"
                    type="button"
                    disabled
                  >
                    Purchase coming next
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="account-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Profile</span>
              <h2>Account details</h2>
            </div>
          </div>

          <div className="details-grid">
            <div>
              <span>Email</span>
              <strong>{user?.email}</strong>
            </div>
            <div>
              <span>Verification</span>
              <strong>
                {user?.is_verified
                  ? "Verified"
                  : "Not verified"}
              </strong>
            </div>
            <div>
              <span>Account status</span>
              <strong>
                {user?.is_active ? "Active" : "Inactive"}
              </strong>
            </div>
            <div>
              <span>User ID</span>
              <strong className="user-id">
                {user?.id}
              </strong>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}