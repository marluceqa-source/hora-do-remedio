import { Box, CircularProgress } from "@mui/material";
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { ProfessionalRole } from "../api/types";

export function ProtectedRoute({ children, roles }: { children: ReactNode; roles?: ProfessionalRole[] }) {
  const { professional, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <CircularProgress aria-label="Carregando" />
      </Box>
    );
  }

  if (!professional) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(professional.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
