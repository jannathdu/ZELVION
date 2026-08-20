import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";


export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <main className="loading-screen">
        <div className="loading-spinner" aria-hidden="true" />
        <p>Securing your session...</p>
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}