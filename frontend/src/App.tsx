import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AdminPage } from "./pages/AdminPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { MedicationCreatePage } from "./pages/MedicationCreatePage";
import { MedicationDetailPage } from "./pages/MedicationDetailPage";
import { PasswordResetPage } from "./pages/PasswordResetPage";
import { PatientCreatePage } from "./pages/PatientCreatePage";
import { PatientDetailPage } from "./pages/PatientDetailPage";
import { PatientsListPage } from "./pages/PatientsListPage";
import { ProfilePage } from "./pages/ProfilePage";
import { SignupPage } from "./pages/SignupPage";

function Protected({ children, roles }: { children: React.ReactNode; roles?: ("admin" | "medico" | "enfermeiro" | "outro_profissional")[] }) {
  return (
    <ProtectedRoute roles={roles}>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/password-reset" element={<PasswordResetPage />} />

      <Route path="/" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/patients" element={<Protected><PatientsListPage /></Protected>} />
      <Route path="/patients/new" element={<Protected><PatientCreatePage /></Protected>} />
      <Route path="/patients/:patientId" element={<Protected><PatientDetailPage /></Protected>} />
      <Route path="/patients/:patientId/medications/new" element={<Protected><MedicationCreatePage /></Protected>} />
      <Route path="/treatment-medications/:treatmentMedicationId" element={<Protected><MedicationDetailPage /></Protected>} />
      <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />
      <Route path="/admin" element={<Protected roles={["admin"]}><AdminPage /></Protected>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
