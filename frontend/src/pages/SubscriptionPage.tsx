import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  getApiErrorMessage,
  getSubscriptionPlans,
  type SubscriptionPlan,
} from "../api/client";

import {
  getMySubscription,
  renewMySubscription,
  type UserSubscription,
} from "../api/subscriptions";

import { getStoredTokens } from "../auth/tokens";
import { useAuth } from "../auth/AuthContext";


function formatBytes(
  bytes: number | null,
): string {
  if (bytes === null) {
    return "Unlimited";
  }

  return `${(bytes / 1024 ** 3).toFixed(0)} GB`;
}


function formatDate(
  value: string,
): string {
  return new Date(value).toLocaleString();
}


function formatPrice(
  amount: number,
  currency: string,
): string {
  return new Intl.NumberFormat(
    "zh-CN",
    {
      style: "currency",
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    },
  ).format(amount / 100);
}


export function SubscriptionPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const [
    subscription,
    setSubscription,
  ] = useState<UserSubscription | null>(
    null,
  );

  const [plans, setPlans] =
    useState<SubscriptionPlan[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isRenewing, setIsRenewing] =
    useState(false);

  const [isSigningOut, setIsSigningOut] =
    useState(false);

  const [error, setError] =
    useState("");


  async function refreshSubscription():
    Promise<void> {
    const tokens = getStoredTokens();

    if (!tokens) {
      return;
    }

    const [
      subscriptionData,
      planData,
    ] = await Promise.all([
      getMySubscription(
        tokens.accessToken,
      ),
      getSubscriptionPlans(),
    ]);

    setSubscription(
      subscriptionData,
    );

    setPlans(
      planData,
    );
  }


  useEffect(() => {
    async function loadSubscription() {
      try {
        await refreshSubscription();

        setError("");
      } catch {
        setError(
          "Unable to load subscription information.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadSubscription();
  }, []);


  async function handleRenew():
    Promise<void> {
    const tokens = getStoredTokens();

    if (
      !tokens ||
      !subscription ||
      isRenewing
    ) {
      return;
    }

    setIsRenewing(true);
    setError("");

    try {
      const renewedSubscription =
        await renewMySubscription(
          tokens.accessToken,
        );

      setSubscription(
        renewedSubscription,
      );

      alert(
        "Subscription renewed successfully.",
      );
    } catch (error) {
      setError(
        getApiErrorMessage(
          error,
          "Subscription renewal failed.",
        ),
      );
    } finally {
      setIsRenewing(false);
    }
  }


  async function handleSignOut():
    Promise<void> {
    setIsSigningOut(true);

    await signOut();

    navigate(
      "/login",
      {
        replace: true,
      },
    );
  }


  const currentPlan =
    subscription
      ? plans.find(
          (plan) =>
            plan.id ===
            subscription.plan_id,
        ) ?? null
      : null;


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
              className="nav-item"
              to="/devices"
            >
              Devices
            </Link>

            <Link
              className="nav-item active"
              to="/subscription"
            >
              Subscription
            </Link>

            <Link
              className="nav-item"
              to="/usage"
            >
              Usage
            </Link>

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
              Subscription
            </span>

            <h1>
              Your subscription
            </h1>

            <p>
              Review your active plan,
              renewal period, data quota
              and device allowance.
            </p>

          </div>

        </header>


        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        {
          isLoading ? (

            <p>
              Loading subscription...
            </p>

          ) : subscription === null ? (

            <section className="account-section">

              <h2>
                No active subscription
              </h2>

              <p>
                Choose a plan from your
                dashboard to activate ZELVION.
              </p>

              <Link
                className="plan-button"
                to="/dashboard"
              >
                View Plans
              </Link>

            </section>

          ) : (

            <>

              <section className="status-grid">

                <article className="status-card">

                  <div className="card-label">
                    Current Plan
                  </div>

                  <strong className="card-value">
                    {
                      currentPlan?.name
                      ?? "Active Plan"
                    }
                  </strong>

                  <p>
                    Status:{" "}
                    {subscription.status}
                  </p>

                </article>


                <article className="status-card">

                  <div className="card-label">
                    Price
                  </div>

                  <strong className="card-value">
                    {
                      formatPrice(
                        subscription
                          .price_minor_units,
                        subscription
                          .currency,
                      )
                    }
                  </strong>

                  <p>
                    {
                      subscription
                        .duration_days
                    } days
                  </p>

                </article>


                <article className="status-card">

                  <div className="card-label">
                    Data Limit
                  </div>

                  <strong className="card-value">
                    {
                      formatBytes(
                        subscription
                          .data_limit_bytes,
                      )
                    }
                  </strong>

                  <p>
                    Per subscription period
                  </p>

                </article>


                <article className="status-card">

                  <div className="card-label">
                    Devices
                  </div>

                  <strong className="card-value">
                    {
                      subscription
                        .max_devices
                    }
                  </strong>

                  <p>
                    Maximum active devices
                  </p>

                </article>

              </section>


              <section className="account-section">

                <h2>
                  Subscription period
                </h2>

                <p>
                  <strong>
                    Started:
                  </strong>{" "}
                  {
                    formatDate(
                      subscription
                        .starts_at,
                    )
                  }
                </p>

                <p>
                  <strong>
                    Expires:
                  </strong>{" "}
                  {
                    formatDate(
                      subscription
                        .ends_at,
                    )
                  }
                </p>

                <p>
                  <strong>
                    Status:
                  </strong>{" "}
                  {subscription.status}
                </p>


                <button
                  className="plan-button"
                  type="button"
                  disabled={isRenewing}
                  onClick={() =>
                    void handleRenew()
                  }
                >
                  {
                    isRenewing
                      ? "Renewing..."
                      : "Renew Subscription"
                  }
                </button>

                <p>
                  Development renewal only.
                  Production renewal will require
                  a verified payment.
                </p>

              </section>

            </>
          )
        }

      </main>

    </div>
  );
}