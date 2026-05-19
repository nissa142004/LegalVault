import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { authApi, clearToken, getApiError, getToken, saveToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!getToken()) {
        setBooting(false);
        return;
      }

      try {
        const response = await authApi.profile();
        setUser(response.data.user);
      } catch {
        clearToken();
        setUser(null);
      } finally {
        setBooting(false);
      }
    }

    loadUser();
  }, []);

  async function login(credentials) {
    try {
      const response = await authApi.login(credentials);
      saveToken(response.data.token);
      setUser(response.data.user);
      return response.data.user;
    } catch (error) {
      throw new Error(getApiError(error, "Unable to log in."));
    }
  }

  async function register(payload) {
    try {
      const response = await authApi.register(payload);
      saveToken(response.data.token);
      setUser(response.data.user);
      return response.data.user;
    } catch (error) {
      throw new Error(getApiError(error, "Unable to create account."));
    }
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  const value = useMemo(
    () => ({
      booting,
      isAuthenticated: Boolean(user),
      login,
      logout,
      register,
      user,
    }),
    [booting, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
