import { Box, Chip, Paper, Stack, Typography } from "@mui/material";
import { useAuth } from "../context/AuthContext";

export function ProfilePage() {
  const { professional } = useAuth();
  if (!professional) return null;

  return (
    <Box sx={{ maxWidth: "sm" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Meu perfil
      </Typography>
      <Paper sx={{ p: 3 }} variant="outlined">
        <Stack spacing={1.5}>
          <Typography>
            <strong>Nome:</strong> {professional.full_name}
          </Typography>
          <Typography>
            <strong>E-mail:</strong> {professional.email}
          </Typography>
          <Typography>
            <strong>Papel:</strong> {professional.role}
          </Typography>
          <Typography>
            <strong>Profissão:</strong> {professional.profession}
          </Typography>
          {professional.council_number && (
            <Typography>
              <strong>Conselho:</strong> {professional.council_type} {professional.council_number}/
              {professional.council_state}
            </Typography>
          )}
          <Box>
            <Chip
              label={`Verificação: ${professional.verification_status}`}
              color={professional.verification_status === "verified" ? "success" : "warning"}
              sx={{ mr: 1 }}
            />
            <Chip
              label={professional.mfa_enabled ? "MFA ativo" : "MFA inativo"}
              color={professional.mfa_enabled ? "success" : "default"}
            />
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}
