import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { QRCodeSVG } from "qrcode.react";
import { Link as RouterLink, useParams } from "react-router-dom";
import { createPatientInvite, getPatient, getPatientHistory, listPatientMedications } from "../api/patients";
import type { Patient, PatientInvite, ReminderEvent, TreatmentMedication } from "../api/types";
import { extractErrorMessage } from "../api/client";

const STATUS_LABEL: Record<TreatmentMedication["status"], string> = {
  draft: "Rascunho",
  pending_validation: "Aguardando validação",
  active: "Ativo",
  suspended: "Suspenso",
  closed: "Encerrado",
};

const REMINDER_STATUS_LABEL: Record<ReminderEvent["status"], string> = {
  pending: "Pendente",
  delivered: "Entregue, sem confirmação",
  confirmed: "Confirmado",
  not_taken: "Não tomado (declarado)",
  snoozed: "Adiado",
  expired: "Expirado",
};

function TelegramLinkSection({ patient }: { patient: Patient }) {
  const [invite, setInvite] = useState<PatientInvite | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerateInvite = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await createPatientInvite(patient.id);
      setInvite(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (patient.telegram_link_status === "linked") {
    return <Alert severity="success">Paciente vinculado ao Telegram.</Alert>;
  }

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Gere um convite de uso único para o paciente vincular a conta do Telegram (RF04). O bot
        nunca envia dados de saúde antes dessa confirmação.
      </Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {!invite ? (
        <Button variant="contained" onClick={handleGenerateInvite} disabled={loading}>
          Gerar convite
        </Button>
      ) : (
        <Paper variant="outlined" sx={{ p: 2, mt: 1, display: "inline-block" }}>
          {invite.telegram_deep_link ? (
            <>
              <QRCodeSVG value={invite.telegram_deep_link} size={180} />
              <Typography variant="body2" sx={{ mt: 1, wordBreak: "break-all" }}>
                <a href={invite.telegram_deep_link} target="_blank" rel="noreferrer">
                  {invite.telegram_deep_link}
                </a>
              </Typography>
            </>
          ) : (
            <Typography variant="body2">{invite.instructions}</Typography>
          )}
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
            Válido até {new Date(invite.expires_at).toLocaleString("pt-BR")}
          </Typography>
        </Paper>
      )}
    </Box>
  );
}

export function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const id = Number(patientId);

  const [patient, setPatient] = useState<Patient | null>(null);
  const [medications, setMedications] = useState<TreatmentMedication[]>([]);
  const [history, setHistory] = useState<ReminderEvent[]>([]);
  const [tab, setTab] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [patientData, medicationsData, historyData] = await Promise.all([
        getPatient(id),
        listPatientMedications(id),
        getPatientHistory(id, "month"),
      ]);
      setPatient(patientData);
      setMedications(medicationsData);
      setHistory(historyData);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <Alert severity="error">{error}</Alert>;
  if (!patient) return null;

  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        {patient.full_name}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Identificador: {patient.internal_identifier}
      </Typography>

      <Tabs value={tab} onChange={(_, value) => setTab(value)} sx={{ mb: 2 }}>
        <Tab label="Vínculo Telegram" />
        <Tab label="Medicamentos" />
        <Tab label="Histórico" />
      </Tabs>

      {tab === 0 && <TelegramLinkSection patient={patient} />}

      {tab === 1 && (
        <Box>
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
            <Button
              component={RouterLink}
              to={`/patients/${id}/medications/new`}
              variant="contained"
              startIcon={<AddIcon />}
            >
              Cadastrar medicamento
            </Button>
          </Box>
          <Paper variant="outlined">
            <List aria-label="Medicamentos do paciente">
              {medications.length === 0 && (
                <Box sx={{ p: 2 }}>
                  <Typography color="text.secondary">Nenhum medicamento cadastrado ainda.</Typography>
                </Box>
              )}
              {medications.map((medication) => (
                <ListItemButton
                  key={medication.id}
                  component={RouterLink}
                  to={`/treatment-medications/${medication.id}`}
                >
                  <ListItemText
                    primary={medication.medication_name}
                    secondary={`${medication.dosage} ${medication.dosage_unit ?? ""} — ${medication.quantity_per_administration}`}
                  />
                  <Chip label={STATUS_LABEL[medication.status]} size="small" />
                </ListItemButton>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {tab === 2 && (
        <Paper variant="outlined">
          <List aria-label="Histórico de doses">
            {history.length === 0 && (
              <Box sx={{ p: 2 }}>
                <Typography color="text.secondary">Sem histórico no período.</Typography>
              </Box>
            )}
            {history.map((event) => (
              <Box key={event.id} sx={{ px: 2, py: 1, borderBottom: "1px solid", borderColor: "divider" }}>
                <Typography variant="body2">
                  Programado: {new Date(event.scheduled_datetime).toLocaleString("pt-BR")}
                  {event.confirmed_datetime && (
                    <> — Confirmado: {new Date(event.confirmed_datetime).toLocaleString("pt-BR")}</>
                  )}
                </Typography>
                <Chip label={REMINDER_STATUS_LABEL[event.status]} size="small" sx={{ mt: 0.5 }} />
              </Box>
            ))}
          </List>
        </Paper>
      )}
    </>
  );
}
