import { useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";


type LocationState = {
  message?: string;
};

export function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const locationState = location.state as LocationState | null;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await signIn(email, password);
      navigate("/dashboard", { replace: true });
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError(
          "Unable to connect to ZELVION. Please try again.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <Link className="brand" to="/">
          <span className="brand-mark">Z</span>
          <span>ZELVION</span>
        </Link>

        <div className="brand-message">
          <span className="eyebrow">Private by design</span>
          <h1>Your secure connection starts here.</h1>
          <p>
            Manage your account, devices, and protected
            connections from one clear dashboard.
          </p>
        </div>

        <div className="security-note">
          <span className="security-dot" />
          Secure authentication with rotating sessions
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-heading">
            <span className="eyebrow">Welcome back</span>
            <h2>Sign in to ZELVION</h2>
            <p>Enter your account details to continue.</p>
          </div>

          {locationState?.message && (
            <div className="success-message" role="status">
              {locationState.message}
            </div>
          )}

          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
              required
            />

            <label htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              placeholder="Enter your password"
              required
            />

            <button
              className="primary-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="auth-switch">
            New to ZELVION?{" "}
            <Link to="/register">Create an account</Link>
          </p>
        </div>
      </section>
    </main>
  );
}