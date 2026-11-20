import { useState } from "react";
import { Alert, Box, Button, Paper, TextField, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { createPatient } from "../api/patients";
import { extractErrorMessage } from "../api/client";

export function PatientCreatePage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [internalIdentifier, setInternalIdentifier] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [contact, setContact] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ fullName?: string; internalIdentifier?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const nextFieldErrors: { fullName?: string; internalIdentifier?: string } = {};
    if (!fullName.trim()) nextFieldErrors.fullName = "Informe o nome completo";
    if (!internalIdentifier.trim()) nextFieldErrors.internalIdentifier = "Informe o identificador interno";
    setFieldErrors(nextFieldErrors);
    if (Object.keys(nextFieldErrors).length > 0) return;

    setSubmitting(true);
    try {
      const patient = await createPatient({
        full_name: fullName,
        internal_identifier: internalIdentifier,
        birth_date: birthDate || null,
        contact: contact || null,
      });
      navigate(`/patients/${patient.id}`);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: "sm" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Cadastrar paciente
      </Typography>
      <Paper sx={{ p: 3 }} variant="outlined">
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} role="alert">
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Nome completo"
            fullWidth
            required
            autoFocus
            margin="normal"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            error={!!fieldErrors.fullName}
            helperText={fieldErrors.fullName}
          />
          <TextField
            label="Identificador interno"
            fullWidth
            required
            margin="normal"
            helperText={fieldErrors.internalIdentifier ?? "Único — nunca use CPF ou outro documento"}
            error={!!fieldErrors.internalIdentifier}
            value={internalIdentifier}
            onChange={(e) => setInternalIdentifier(e.target.value)}
          />
          <TextField
            label="Data de nascimento"
            type="date"
            fullWidth
            margin="normal"
            slotProps={{ inputLabel: { shrink: true } }}
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
          />
          <TextField
            label="Contato (opcional, só se autorizado)"
            fullWidth
            margin="normal"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
          />
          <Button type="submit" variant="contained" size="large" sx={{ mt: 2 }} disabled={submitting}>
            Cadastrar
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
