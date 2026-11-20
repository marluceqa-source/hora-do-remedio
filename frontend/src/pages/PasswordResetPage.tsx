import { useState } from "react";
import { Alert, Box, Button, Container, Paper, TextField, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { confirmPasswordReset, requestPasswordReset } from "../api/auth";
import { extractErrorMessage } from "../api/client";

export function PasswordResetPage() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [requestSent, setRequestSent] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; token?: string; newPassword?: string }>({});

  const handleRequest = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!email.trim()) {
      setFieldErrors({ email: "Informe o e-mail" });
      return;
    }
    setFieldErrors({});
    try {
      await requestPasswordReset(email);
      setRequestSent(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleConfirm = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const nextFieldErrors: { token?: string; newPassword?: string } = {};
    if (!token.trim()) nextFieldErrors.token = "Informe o token de recuperação";
    if (newPassword.length < 8) nextFieldErrors.newPassword = "A senha deve ter pelo menos 8 caracteres";
    setFieldErrors(nextFieldErrors);
    if (Object.keys(nextFieldErrors).length > 0) return;

    try {
      await confirmPasswordReset(token, newPassword);
      setConfirmed(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Paper component="main" sx={{ p: 4 }} elevation={2}>
        <Typography variant="h5" component="h1" gutterBottom>
          Recuperar acesso
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} role="alert">
            {error}
          </Alert>
        )}

        {!requestSent ? (
          <Box component="form" onSubmit={handleRequest} sx={{ mt: 2 }} noValidate>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Informe seu e-mail. Se existir uma conta, instruções de recuperação são geradas.
            </Typography>
            <TextField
              label="E-mail"
              type="email"
              fullWidth
              required
              autoFocus
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
            />
            <Button type="submit" fullWidth variant="contained" sx={{ mt: 2 }}>
              Solicitar recuperação
            </Button>
          </Box>
        ) : !confirmed ? (
          <Box component="form" onSubmit={handleConfirm} sx={{ mt: 2 }} noValidate>
            <Alert severity="info" sx={{ mb: 2 }}>
              Se o e-mail existir, um token foi gerado (consulte o administrador do sistema — este
              ambiente não envia e-mails reais). Cole o token recebido abaixo.
            </Alert>
            <TextField
              label="Token de recuperação"
              fullWidth
              required
              margin="normal"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              error={!!fieldErrors.token}
              helperText={fieldErrors.token}
            />
            <TextField
              label="Nova senha"
              type="password"
              fullWidth
              required
              margin="normal"
              helperText={fieldErrors.newPassword ?? "Mínimo de 8 caracteres"}
              error={!!fieldErrors.newPassword}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <Button type="submit" fullWidth variant="contained" sx={{ mt: 2 }}>
              Definir nova senha
            </Button>
          </Box>
        ) : (
          <Alert severity="success" sx={{ mt: 2 }}>
            Senha redefinida com sucesso. Todas as sessões anteriores foram encerradas.
          </Alert>
        )}

        <Button component={RouterLink} to="/login" fullWidth sx={{ mt: 2 }}>
          Voltar ao login
        </Button>
      </Paper>
    </Container>
  );
}
