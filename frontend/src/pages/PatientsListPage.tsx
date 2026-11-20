import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { Link as RouterLink } from "react-router-dom";
import { listPatients } from "../api/patients";
import type { Patient } from "../api/types";
import { extractErrorMessage } from "../api/client";

const LINK_STATUS_LABEL: Record<Patient["telegram_link_status"], string> = {
  not_linked: "Não vinculado",
  invited: "Convite enviado",
  linked: "Vinculado",
};

const LINK_STATUS_COLOR: Record<Patient["telegram_link_status"], "default" | "warning" | "success"> = {
  not_linked: "default",
  invited: "warning",
  linked: "success",
};

export function PatientsListPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listPatients()
      .then(setPatients)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h4" component="h1">
          Pacientes
        </Typography>
        <Button component={RouterLink} to="/patients/new" variant="contained" startIcon={<AddIcon />}>
          Cadastrar paciente
        </Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      {!loading && patients.length === 0 && !error && (
        <Alert severity="info">Você ainda não tem pacientes vinculados.</Alert>
      )}

      <Paper variant="outlined">
        <List aria-label="Lista de pacientes">
          {patients.map((patient) => (
            <ListItemButton key={patient.id} component={RouterLink} to={`/patients/${patient.id}`}>
              <ListItemText primary={patient.full_name} secondary={`Identificador: ${patient.internal_identifier}`} />
              <Chip
                label={LINK_STATUS_LABEL[patient.telegram_link_status]}
                color={LINK_STATUS_COLOR[patient.telegram_link_status]}
                size="small"
              />
            </ListItemButton>
          ))}
        </List>
      </Paper>
    </>
  );
}
