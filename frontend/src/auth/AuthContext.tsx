/* eslint-disable react-refresh/only-export-components */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  ApiError,
  getCurrentUser,
  login,
  logout,
  refresh,
  register,
  type User,
} from "../api/client";
import {
  clearTokens,
  getStoredTokens,
  saveTokens,
} from "./tokens";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function restoreSession(): Promise<void> {
      const tokens = getStoredTokens();

      if (!tokens) {
        if (isActive) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const currentUser = await getCurrentUser(
          tokens.accessToken,
        );

        if (isActive) {
          setUser(currentUser);
        }
      } catch (error) {
        if (
          error instanceof ApiError
          && error.status === 401
        ) {
          try {
            const newTokens = await refresh(
              tokens.refreshToken,
            );
            saveTokens(newTokens);

            const currentUser = await getCurrentUser(
              newTokens.access_token,
            );

            if (isActive) {
              setUser(currentUser);
            }
          } catch {
            clearTokens();
          }
        } else {
          clearTokens();
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      isActive = false;
    };
  }, []);

  async function signIn(
    email: string,
    password: string,
  ): Promise<void> {
    const tokens = await login(email, password);
    saveTokens(tokens);

    try {
      const currentUser = await getCurrentUser(
        tokens.access_token,
      );
      setUser(currentUser);
    } catch (error) {
      clearTokens();
      throw error;
    }
  }

  async function signUp(
    email: string,
    password: string,
  ): Promise<void> {
    await register(email, password);
    await signIn(email, password);
  }

  async function signOut(): Promise<void> {
    const tokens = getStoredTokens();

    clearTokens();
    setUser(null);

    if (tokens) {
      try {
        await logout(tokens.refreshToken);
      } catch {
        // Local session is already cleared.
      }
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}