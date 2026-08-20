import { useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";


export function RegisterPage() {
  const { user, signUp } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");
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

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await signUp(email, password);
      navigate("/dashboard", { replace: true });
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError(
          "Unable to create your account. Please try again.",
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
          <span className="eyebrow">Built for trust</span>
          <h1>Privacy that stays under your control.</h1>
          <p>
            Create your secure account and prepare to
            protect every supported device.
          </p>
        </div>

        <div className="security-note">
          <span className="security-dot" />
          Passwords protected with Argon2 hashing
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-heading">
            <span className="eyebrow">Get started</span>
            <h2>Create your account</h2>
            <p>
              Use a strong password to protect your access.
            </p>
          </div>

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
              autoComplete="new-password"
              placeholder="Create a strong password"
              minLength={12}
              maxLength={128}
              required
            />

            <p className="field-hint">
              At least 12 characters with uppercase,
              lowercase, number, and special character.
            </p>

            <label htmlFor="confirm-password">
              Confirm password
            </label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(event.target.value)
              }
              autoComplete="new-password"
              placeholder="Enter the password again"
              minLength={12}
              maxLength={128}
              required
            />

            <button
              className="primary-button"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Creating account..."
                : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account?{" "}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </section>
    </main>
  );
}