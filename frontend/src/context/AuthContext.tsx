import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { getMyProfile, logout as apiLogout } from "../api/auth";
import type { Professional } from "../api/types";

interface AuthContextValue {
  professional: Professional | null;
  loading: boolean;
  refresh: () => Promise<void>;
  setProfessional: (professional: Professional | null) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [professional, setProfessional] = useState<Professional | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await getMyProfile();
      setProfessional(data);
    } catch {
      setProfessional(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const logout = useCallback(async () => {
    await apiLogout();
    setProfessional(null);
  }, []);

  return (
    <AuthContext.Provider value={{ professional, loading, refresh, setProfessional, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth precisa estar dentro de um AuthProvider");
  return context;
}
