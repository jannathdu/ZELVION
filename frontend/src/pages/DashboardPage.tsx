import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createPaymentOrder,
  completePayment,
} from "../api/payments";

import { getStoredTokens } from "../auth/tokens";

import {
  getDashboard,
  type DashboardData,
} from "../api/dashboard";

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


function formatGB(bytes: number | null): string {
  if (bytes === null) {
    return "Unlimited";
  }

  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}


export function DashboardPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const [isSigningOut, setIsSigningOut] =
    useState(false);

  const [plans, setPlans] =
    useState<SubscriptionPlan[]>([]);

  const [plansError, setPlansError] =
    useState("");

  const [arePlansLoading, setArePlansLoading] =
    useState(true);

  const [currentPaymentId, setCurrentPaymentId] =
    useState<string | null>(null);

  const [
    currentPaymentPlanId,
    setCurrentPaymentPlanId,
  ] = useState<string | null>(null);

  const [
    isCreatingPayment,
    setIsCreatingPayment,
  ] = useState(false);

  const [
    isCompletingPayment,
    setIsCompletingPayment,
  ] = useState(false);

  const [dashboard, setDashboard] =
    useState<DashboardData | null>(null);

  const [dashboardError, setDashboardError] =
    useState("");

  const [
    isDashboardLoading,
    setIsDashboardLoading,
  ] = useState(true);


  async function refreshDashboard(): Promise<void> {
    const tokens = getStoredTokens();

    if (!tokens) {
      return;
    }

    const data = await getDashboard(
      tokens.accessToken,
    );

    setDashboard(data);
    setDashboardError("");
  }


  useEffect(() => {
    async function loadPlans() {
      try {
        const data =
          await getSubscriptionPlans();

        setPlans(data);
      } catch {
        setPlansError(
          "Plans are temporarily unavailable.",
        );
      } finally {
        setArePlansLoading(false);
      }
    }

    void loadPlans();
  }, []);


  useEffect(() => {
    async function loadDashboard() {
      try {
        await refreshDashboard();
      } catch {
        setDashboardError(
          "Dashboard data unavailable.",
        );
      } finally {
        setIsDashboardLoading(false);
      }
    }

    void loadDashboard();
  }, []);


  async function handleSubscribe(
    planId: string,
  ): Promise<void> {
    if (isCreatingPayment) {
      return;
    }

    const tokens = getStoredTokens();

    if (!tokens) {
      return;
    }

    setIsCreatingPayment(true);

    try {
      const payment =
        await createPaymentOrder(
          tokens.accessToken,
          planId,
        );

      setCurrentPaymentId(payment.id);
      setCurrentPaymentPlanId(planId);

      try {
        await refreshDashboard();
      } catch {
        // Payment creation succeeded even if
        // dashboard refresh temporarily fails.
      }

      alert(
        `Payment created: ${payment.status}`,
      );
    } catch {
      alert(
        "Payment creation failed",
      );
    } finally {
      setIsCreatingPayment(false);
    }
  }


  async function handleCompletePayment():
    Promise<void> {
    const tokens = getStoredTokens();

    if (
      !tokens ||
      !currentPaymentId ||
      isCompletingPayment
    ) {
      return;
    }

    setIsCompletingPayment(true);

    try {
      const payment =
        await completePayment(
          tokens.accessToken,
          currentPaymentId,
        );

      /*
       * Clear the pending payment only AFTER
       * the backend confirms success.
       */
      setCurrentPaymentId(null);
      setCurrentPaymentPlanId(null);

      /*
       * Reload the dashboard so the new
       * subscription, device limit,
       * data quota and payment status
       * appear immediately.
       */
      await refreshDashboard();

      alert(
        `Payment status: ${payment.status}`,
      );
    } catch {
      alert(
        "Payment completion failed",
      );
    } finally {
      setIsCompletingPayment(false);
    }
  }


  async function handleSignOut() {
    setIsSigningOut(true);

    await signOut();

    navigate(
      "/login",
      {
        replace: true,
      },
    );
  }


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

            <a className="nav-item active">
              Overview
            </a>

            <a className="nav-item">
              Devices
            </a>

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
            onClick={() =>
              void handleSignOut()
            }
            disabled={isSigningOut}
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
              Account overview
            </span>

            <h1>
              Welcome to ZELVION
            </h1>

            <p>
              Manage your subscription,
              devices and protected connections.
            </p>

          </div>

        </header>


        {dashboardError && (
          <div className="error-message">
            {dashboardError}
          </div>
        )}


        <section className="status-grid">

          <article className="status-card">

            <div className="card-label">
              Subscription
            </div>

            <strong className="card-value">
              {
                isDashboardLoading
                  ? "Loading..."
                  : dashboard
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


          <article className="status-card">

            <div className="card-label">
              Devices
            </div>

            <strong className="card-value">
              {
                dashboard
                  ? `${dashboard.devices.total_devices}/${dashboard.devices.max_devices ?? "∞"}`
                  : "Loading..."
              }
            </strong>

            <p>
              Registered devices
            </p>

          </article>


          <article className="status-card">

            <div className="card-label">
              Data Usage
            </div>

            <strong className="card-value">
              {
                formatGB(
                  dashboard
                    ?.usage
                    .used_bytes
                    ?? null,
                )
              }
            </strong>

            <p>
              Remaining:{" "}
              {
                formatGB(
                  dashboard
                    ?.usage
                    .remaining_bytes
                    ?? null,
                )
              }
            </p>

          </article>


          <article className="status-card">

            <div className="card-label">
              Payment
            </div>

            <strong className="card-value">
              {
                dashboard
                  ?.payments
                  .last_payment_status
                  ?? "No Payment"
              }
            </strong>

          </article>

        </section>


        <section className="plans-section">

          <div className="section-heading">

            <span className="eyebrow">
              Plans
            </span>

            <h2>
              Choose your access period
            </h2>

          </div>


          {
            arePlansLoading && (
              <p>
                Loading plans...
              </p>
            )
          }


          {
            plansError && (
              <p className="error-message">
                {plansError}
              </p>
            )
          }


          <div className="plans-grid">

            {
              plans.map((plan) => (

                <article
                  className="plan-card"
                  key={plan.id}
                >

                  <h3>
                    {plan.name}
                  </h3>

                  <div className="plan-price">
                    {formatPrice(plan)}
                  </div>

                  <p>
                    {plan.description}
                  </p>

                  <ul>

                    <li>
                      {plan.duration_days} days
                    </li>

                    <li>
                      {
                        formatDataLimit(
                          plan.data_limit_bytes,
                        )
                      }
                    </li>

                    <li>
                      {plan.max_devices} devices
                    </li>

                  </ul>


                  <button
                    className="plan-button"
                    type="button"
                    disabled={
                      isCreatingPayment ||
                      isCompletingPayment
                    }
                    onClick={() =>
                      void handleSubscribe(
                        plan.id,
                      )
                    }
                  >
                    {
                      isCreatingPayment &&
                      currentPaymentPlanId === plan.id
                        ? "Creating Payment..."
                        : "Subscribe"
                    }
                  </button>


                  {
                    currentPaymentId &&
                    currentPaymentPlanId ===
                      plan.id && (
                      <button
                        className="plan-button"
                        type="button"
                        disabled={
                          isCompletingPayment
                        }
                        onClick={() =>
                          void handleCompletePayment()
                        }
                      >
                        {
                          isCompletingPayment
                            ? "Completing..."
                            : "Complete Payment"
                        }
                      </button>
                    )
                  }

                </article>

              ))
            }

          </div>

        </section>


        <section className="account-section">

          <h2>
            Account details
          </h2>

          <p>
            Email: {user?.email}
          </p>

          <p>
            Status:{" "}
            {
              user?.is_active
                ? "Active"
                : "Inactive"
            }
          </p>

        </section>

      </main>

    </div>
  );
}