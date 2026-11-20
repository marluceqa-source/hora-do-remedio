import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Box, Button, Container, MenuItem, Paper, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link as RouterLink } from "react-router-dom";
import { z } from "zod";
import { signup } from "../api/auth";
import { extractErrorMessage } from "../api/client";
import type { ProfessionalRole } from "../api/types";

const ROLES: { value: ProfessionalRole; label: string }[] = [
  { value: "medico", label: "Médico(a)" },
  { value: "enfermeiro", label: "Enfermeiro(a)" },
  { value: "outro_profissional", label: "Outro profissional de saúde" },
  { value: "admin", label: "Administrador" },
];

// Mesmas regras do backend (api/schemas/professional.py) — validadas aqui antes de qualquer
// chamada à API, para a pessoa nunca ver um erro de validação cru do servidor.
const signupSchema = z.object({
  full_name: z.string().min(1, "Informe o nome completo"),
  email: z.string().email("Informe um e-mail válido"),
  password: z.string().min(8, "A senha deve ter pelo menos 8 caracteres"),
  role: z.enum(["medico", "enfermeiro", "outro_profissional", "admin"]),
  profession: z.string().min(1, "Informe a profissão"),
  council_number: z.string().optional(),
  council_state: z.string().max(2, "Use só a sigla, com 2 letras").optional(),
});

type SignupFormValues = z.infer<typeof signupSchema>;

export function SignupPage() {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      role: "medico",
      profession: "",
      council_number: "",
      council_state: "",
    },
  });

  const onSubmit = async (values: SignupFormValues) => {
    setError(null);
    try {
      await signup({
        ...values,
        council_number: values.council_number || undefined,
        council_state: values.council_state || undefined,
      });
      setSuccess(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  if (success) {
    return (
      <Container maxWidth="xs" sx={{ mt: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Alert severity="success">
            Cadastro recebido! Sua conta ainda precisa ser verificada por um administrador antes de
            ter acesso clínico pleno — isso não concede permissões automaticamente.
          </Alert>
          <Button component={RouterLink} to="/login" fullWidth sx={{ mt: 3 }}>
            Ir para o login
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="xs" sx={{ mt: 4, mb: 4 }}>
      <Paper component="main" sx={{ p: 4 }} elevation={2}>
        <Typography variant="h5" component="h1" gutterBottom>
          Criar conta de profissional
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} role="alert">
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 2 }} noValidate>
          <Controller
            name="full_name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Nome completo"
                fullWidth
                required
                margin="normal"
                error={!!errors.full_name}
                helperText={errors.full_name?.message}
              />
            )}
          />
          <Controller
            name="email"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="E-mail"
                type="email"
                fullWidth
                required
                margin="normal"
                error={!!errors.email}
                helperText={errors.email?.message}
              />
            )}
          />
          <Controller
            name="password"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Senha"
                type="password"
                fullWidth
                required
                margin="normal"
                error={!!errors.password}
                helperText={errors.password?.message ?? "Mínimo de 8 caracteres"}
              />
            )}
          />
          <Controller
            name="role"
            control={control}
            render={({ field }) => (
              <TextField {...field} select label="Papel" fullWidth required margin="normal">
                {ROLES.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            )}
          />
          <Controller
            name="profession"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Profissão"
                fullWidth
                required
                margin="normal"
                placeholder="Ex.: Médico, Enfermeiro, Fisioterapeuta"
                error={!!errors.profession}
                helperText={errors.profession?.message}
              />
            )}
          />
          <Controller
            name="council_number"
            control={control}
            render={({ field }) => (
              <TextField {...field} label="Número do conselho profissional" fullWidth margin="normal" />
            )}
          />
          <Controller
            name="council_state"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="UF do conselho"
                fullWidth
                margin="normal"
                slotProps={{ htmlInput: { maxLength: 2 } }}
                onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                error={!!errors.council_state}
                helperText={errors.council_state?.message}
              />
            )}
          />
          <Button type="submit" fullWidth variant="contained" size="large" sx={{ mt: 3 }} disabled={isSubmitting}>
            Criar conta
          </Button>
          <Button component={RouterLink} to="/login" fullWidth sx={{ mt: 1 }}>
            Já tenho conta
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
