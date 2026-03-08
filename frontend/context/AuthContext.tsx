"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export interface AuthUser {
  id: string;
  email: string;
  totp_enabled: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "taxapp_access_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: try restoring token from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      fetchUser(stored)
        .then((u) => {
          setToken(stored);
          setUser(u);
        })
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function fetchUser(accessToken: string): Promise<AuthUser> {
    const res = await fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!res.ok) throw new Error("Unauthorized");
    return res.json() as Promise<AuthUser>;
  }

  async function login(accessToken: string) {
    const u = await fetchUser(accessToken);
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
    setUser(u);
  }

  async function logout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      // swallow — server might already be down
    }
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
