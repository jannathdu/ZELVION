import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  getPaymentHistory,
  type PaymentOrder,
} from "../api/payments";

import {
  getUsageSummary,
  type UsageSummary,
} from "../api/usage";

import { getStoredTokens } from "../auth/tokens";
import { useAuth } from "../auth/AuthContext";


function formatBytes(bytes: number | null): string {
  if (bytes === null) {
    return "Unlimited";
  }

  const gigabytes = bytes / 1024 ** 3;

  return `${gigabytes.toFixed(2)} GB`;
}


function formatPaymentAmount(
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


function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return new Date(value).toLocaleString();
}


export function UsagePage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const [usage, setUsage] =
    useState<UsageSummary | null>(null);

  const [payments, setPayments] =
    useState<PaymentOrder[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [isSigningOut, setIsSigningOut] =
    useState(false);


  useEffect(() => {
    async function loadData() {
      const tokens = getStoredTokens();

      if (!tokens) {
        setIsLoading(false);
        return;
      }

      try {
        const [
          usageData,
          paymentData,
        ] = await Promise.all([
          getUsageSummary(
            tokens.accessToken,
          ),
          getPaymentHistory(
            tokens.accessToken,
          ),
        ]);

        setUsage(usageData);
        setPayments(paymentData.payments);
        setError("");

      } catch {
        setError(
          "Unable to load usage or payment information.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadData();
  }, []);


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


  const usagePercent =
    usage?.limit_bytes &&
    usage.limit_bytes > 0
      ? Math.min(
          100,
          (
            usage.used_bytes /
            usage.limit_bytes
          ) * 100,
        )
      : 0;


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

            <a className="nav-item">
              Subscription
            </a>

            <Link
              className="nav-item active"
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
              Account usage
            </span>

            <h1>
              Usage & payments
            </h1>

            <p>
              Review your current data quota
              and recent payment activity.
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
              Data Used
            </div>

            <strong className="card-value">
              {
                isLoading
                  ? "Loading..."
                  : formatBytes(
                      usage?.used_bytes ?? 0,
                    )
              }
            </strong>

            <p>
              Current subscription
            </p>

          </article>


          <article className="status-card">

            <div className="card-label">
              Data Limit
            </div>

            <strong className="card-value">
              {
                isLoading
                  ? "Loading..."
                  : formatBytes(
                      usage?.limit_bytes
                      ?? null,
                    )
              }
            </strong>

            <p>
              Plan quota
            </p>

          </article>


          <article className="status-card">

            <div className="card-label">
              Remaining
            </div>

            <strong className="card-value">
              {
                isLoading
                  ? "Loading..."
                  : formatBytes(
                      usage?.remaining_bytes
                      ?? null,
                    )
              }
            </strong>

            <p>
              Available data
            </p>

          </article>


          <article className="status-card">

            <div className="card-label">
              Usage
            </div>

            <strong className="card-value">
              {
                `${usagePercent.toFixed(1)}%`
              }
            </strong>

            <p>
              Quota consumed
            </p>

          </article>

        </section>


        <section className="plans-section">

          <div className="section-heading">

            <span className="eyebrow">
              Billing
            </span>

            <h2>
              Payment history
            </h2>

          </div>


          {
            isLoading ? (
              <p>
                Loading payment history...
              </p>
            ) : payments.length === 0 ? (
              <p>
                No payment history yet.
              </p>
            ) : (
              <div className="plans-grid">

                {
                  payments.map(
                    (payment) => (

                      <article
                        className="plan-card"
                        key={payment.id}
                      >

                        <h3>
                          {
                            formatPaymentAmount(
                              payment.amount,
                              payment.currency,
                            )
                          }
                        </h3>

                        <p>
                          Status:{" "}
                          <strong>
                            {payment.status}
                          </strong>
                        </p>

                        <p>
                          Provider:{" "}
                          <strong>
                            {payment.provider}
                          </strong>
                        </p>

                        <p>
                          Created:{" "}
                          {
                            formatDate(
                              payment.created_at,
                            )
                          }
                        </p>

                        <p>
                          Paid:{" "}
                          {
                            formatDate(
                              payment.paid_at,
                            )
                          }
                        </p>

                        {
                          payment.provider_transaction_id && (
                            <p>
                              Transaction:{" "}
                              {
                                payment
                                  .provider_transaction_id
                              }
                            </p>
                          )
                        }

                      </article>

                    ),
                  )
                }

              </div>
            )
          }

        </section>

      </main>

    </div>
  );
}