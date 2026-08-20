import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";


export function DashboardPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [isSigningOut, setIsSigningOut] = useState(false);

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
              Your secure workspace is ready. Service
              features will appear here as they are enabled.
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
            <button className="secondary-button" type="button" disabled>
              Connect unavailable
            </button>
          </article>

          <article className="status-card">
            <div className="card-label">Subscription</div>
            <strong className="card-value">No active plan</strong>
            <p>
              Subscription plans will be available in the
              next development phase.
            </p>
          </article>

          <article className="status-card" id="devices">
            <div className="card-label">Registered devices</div>
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
              <strong className="user-id">{user?.id}</strong>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}