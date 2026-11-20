import { useCallback, useEffect, useState } from "react";
import { Alert, Box, Button, Chip, Divider, Paper, Stack, Typography } from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import {
  activateTreatmentMedication,
  getTreatmentMedicationVersions,
  suspendTreatmentMedication,
} from "../api/treatments";
import type { TreatmentMedication } from "../api/types";
import { extractErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

function describeSchedule(schedule: TreatmentMedication["schedules"][number]): string {
  if (schedule.recurrence_type === "daily") return `Diariamente às ${schedule.schedule_time?.slice(0, 5)}`;
  if (schedule.recurrence_type === "weekly") {
    return `Às ${schedule.schedule_time?.slice(0, 5)} em ${schedule.weekdays}`;
  }
  return `A cada ${schedule.interval_hours}h`;
}

export function MedicationDetailPage() {
  const { treatmentMedicationId } = useParams<{ treatmentMedicationId: string }>();
  const id = Number(treatmentMedicationId);
  const navigate = useNavigate();
  const { professional } = useAuth();

  const [versions, setVersions] = useState<TreatmentMedication[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const chain = await getTreatmentMedicationVersions(id);
      setVersions(chain);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const current = versions.find((v) => v.id === id) ?? versions[versions.length - 1];
  const olderVersions = versions.filter((v) => v.id !== current?.id);

  const handleActivate = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await activateTreatmentMedication(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleSuspend = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await suspendTreatmentMedication(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (!current) return null;

  return (
    <Box sx={{ maxWidth: "sm" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {current.medication_name}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} role="alert">
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }} variant="outlined">
        <Stack spacing={1}>
          <Box>
            <Chip label={current.status} color={current.status === "active" ? "success" : "default"} />
          </Box>
          <Typography>
            <strong>Dose:</strong> {current.dosage} {current.dosage_unit ?? ""}
          </Typography>
          <Typography>
            <strong>Quantidade:</strong> {current.quantity_per_administration}
          </Typography>
          {current.instructions && (
            <Typography>
              <strong>Orientações:</strong> {current.instructions}
            </Typography>
          )}
          <Typography>
            <strong>Início:</strong> {current.start_date}
            {current.end_date && <> — <strong>Término:</strong> {current.end_date}</>}
          </Typography>
          <Typography variant="subtitle2" sx={{ mt: 1 }}>
            Horários:
          </Typography>
          {current.schedules.map((schedule) => (
            <Typography key={schedule.id} variant="body2">
              • {describeSchedule(schedule)}
            </Typography>
          ))}
        </Stack>

        <Divider sx={{ my: 2 }} />

        <Stack direction="row" spacing={2}>
          {current.status === "draft" && (
            <Button
              variant="contained"
              onClick={handleActivate}
              disabled={submitting || professional?.role !== "medico"}
              title={professional?.role !== "medico" ? "Só um médico pode ativar (RN20)" : undefined}
            >
              Ativar tratamento
            </Button>
          )}
          {current.status === "active" && (
            <Button variant="outlined" color="warning" onClick={handleSuspend} disabled={submitting}>
              Suspender tratamento
            </Button>
          )}
          <Button variant="text" onClick={() => navigate(-1)}>
            Voltar
          </Button>
        </Stack>
        {current.status === "draft" && professional?.role !== "medico" && (
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
            A ativação clínica depende das atribuições do profissional (RN20) — só um médico pode
            ativar.
          </Typography>
        )}
      </Paper>

      {olderVersions.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Versões anteriores
          </Typography>
          <Stack spacing={1}>
            {olderVersions.map((version) => (
              <Paper key={version.id} variant="outlined" sx={{ p: 2 }}>
                <Typography variant="body2">
                  {version.dosage} {version.dosage_unit ?? ""} — {version.quantity_per_administration}
                </Typography>
                <Chip label={version.status} size="small" sx={{ mt: 0.5 }} />
              </Paper>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}
