import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Container,
  Link as MuiLink,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { QRCodeSVG } from "qrcode.react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { confirmMfaSetup, loginStep1, startMfaSetup, verifyMfa } from "../api/auth";
import { extractErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

type Step = "credentials" | "mfa_setup" | "mfa_verify";

export function LoginPage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();

  const [step, setStep] = useState<Step>("credentials");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [preAuthToken, setPreAuthToken] = useState("");
  const [provisioningUri, setProvisioningUri] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleCredentialsSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password) {
      setError("Preencha o e-mail e a senha.");
      return;
    }
    setSubmitting(true);
    try {
      const challenge = await loginStep1(email, password);
      setPreAuthToken(challenge.pre_auth_token);
      if (challenge.purpose === "mfa_setup") {
        const setup = await startMfaSetup(challenge.pre_auth_token);
        setProvisioningUri(setup.provisioning_uri);
        setStep("mfa_setup");
      } else {
        setStep("mfa_verify");
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleMfaSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!/^\d{6}$/.test(code.trim())) {
      setError("Informe o código de 6 dígitos do aplicativo autenticador.");
      return;
    }
    setSubmitting(true);
    try {
      if (step === "mfa_setup") {
        await confirmMfaSetup(preAuthToken, code);
      } else {
        await verifyMfa(preAuthToken, code);
      }
      await refresh();
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Paper component="main" sx={{ p: 4 }} elevation={2}>
        <Typography variant="h5" component="h1" gutterBottom>
          💊 Hora do Remédio
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Portal de profissionais de saúde
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }} role="alert">
            {error}
          </Alert>
        )}

        {step === "credentials" && (
          <Box component="form" onSubmit={handleCredentialsSubmit} sx={{ mt: 3 }} noValidate>
            <TextField
              label="E-mail"
              type="email"
              fullWidth
              required
              autoFocus
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <TextField
              label="Senha"
              type="password"
              fullWidth
              required
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button type="submit" fullWidth variant="contained" size="large" sx={{ mt: 2 }} disabled={submitting}>
              Entrar
            </Button>
            <Box sx={{ mt: 2, display: "flex", justifyContent: "space-between" }}>
              <MuiLink component={RouterLink} to="/password-reset" variant="body2">
                Esqueci minha senha
              </MuiLink>
              <MuiLink component={RouterLink} to="/signup" variant="body2">
                Criar conta
              </MuiLink>
            </Box>
          </Box>
        )}

        {step === "mfa_setup" && (
          <Box component="form" onSubmit={handleMfaSubmit} sx={{ mt: 3 }} noValidate>
            <Typography variant="body2" gutterBottom>
              Primeiro acesso: configure a autenticação em duas etapas. Escaneie o código abaixo
              em um aplicativo autenticador (Google Authenticator, Authy etc.):
            </Typography>
            <Box sx={{ display: "flex", justifyContent: "center", my: 2 }}>
              <Box sx={{ p: 2, bgcolor: "white", borderRadius: 1, border: "1px solid", borderColor: "divider" }}>
                <QRCodeSVG value={provisioningUri} size={200} />
              </Box>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 2 }}>
              Não consegue escanear? Abra o app autenticador e cole este código manualmente:{" "}
              <Box
                component="span"
                sx={{ fontFamily: "monospace", wordBreak: "break-all" }}
              >
                {provisioningUri}
              </Box>
            </Typography>
            <TextField
              label="Código de 6 dígitos"
              fullWidth
              required
              autoFocus
              margin="normal"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              slotProps={{ htmlInput: { inputMode: "numeric", pattern: "[0-9]*", maxLength: 6 } }}
            />
            <Button type="submit" fullWidth variant="contained" size="large" sx={{ mt: 2 }} disabled={submitting}>
              Confirmar e entrar
            </Button>
          </Box>
        )}

        {step === "mfa_verify" && (
          <Box component="form" onSubmit={handleMfaSubmit} sx={{ mt: 3 }} noValidate>
            <Typography variant="body2" gutterBottom>
              Digite o código do seu aplicativo autenticador.
            </Typography>
            <TextField
              label="Código de 6 dígitos"
              fullWidth
              required
              autoFocus
              margin="normal"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              slotProps={{ htmlInput: { inputMode: "numeric", pattern: "[0-9]*", maxLength: 6 } }}
            />
            <Button type="submit" fullWidth variant="contained" size="large" sx={{ mt: 2 }} disabled={submitting}>
              Entrar
            </Button>
          </Box>
        )}
      </Paper>
    </Container>
  );
}
