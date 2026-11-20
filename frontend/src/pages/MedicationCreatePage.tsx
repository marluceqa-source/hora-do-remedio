import { useState } from "react";
import { Alert, Box, Button, MenuItem, Paper, TextField, Typography } from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import { createTreatmentMedication } from "../api/treatments";
import { extractErrorMessage } from "../api/client";
import type { ScheduleRecurrence } from "../api/types";

export function MedicationCreatePage() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();

  const [medicationName, setMedicationName] = useState("");
  const [dosage, setDosage] = useState("");
  const [dosageUnit, setDosageUnit] = useState("mg");
  const [quantity, setQuantity] = useState("");
  const [instructions, setInstructions] = useState("");
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState("");
  const [recurrenceType, setRecurrenceType] = useState<ScheduleRecurrence>("daily");
  const [scheduleTime, setScheduleTime] = useState("08:00");
  const [intervalHours, setIntervalHours] = useState("8");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    medicationName?: string;
    dosage?: string;
    quantity?: string;
    startDate?: string;
  }>({});
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const nextFieldErrors: typeof fieldErrors = {};
    if (!medicationName.trim()) nextFieldErrors.medicationName = "Informe o nome do medicamento";
    if (!dosage.trim()) nextFieldErrors.dosage = "Informe a dose";
    if (!quantity.trim()) nextFieldErrors.quantity = "Informe a quantidade por administração";
    if (!startDate) nextFieldErrors.startDate = "Informe a data de início";
    setFieldErrors(nextFieldErrors);
    if (Object.keys(nextFieldErrors).length > 0) return;

    setSubmitting(true);
    try {
      const treatment = await createTreatmentMedication(Number(patientId), {
        medication_name: medicationName,
        dosage,
        dosage_unit: dosageUnit || null,
        quantity_per_administration: quantity,
        instructions: instructions || null,
        start_date: startDate,
        end_date: endDate || null,
        schedules: [
          recurrenceType === "interval"
            ? { recurrence_type: "interval", interval_hours: Number(intervalHours) }
            : { recurrence_type: recurrenceType, schedule_time: `${scheduleTime}:00` },
        ],
      });
      navigate(`/treatment-medications/${treatment.id}`);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: "sm" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Cadastrar medicamento
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Fica como rascunho — só gera lembretes depois de revisado e ativado (RN25).
      </Typography>
      <Paper sx={{ p: 3, mt: 2 }} variant="outlined">
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} role="alert">
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Nome do medicamento"
            fullWidth
            required
            autoFocus
            margin="normal"
            value={medicationName}
            onChange={(e) => setMedicationName(e.target.value)}
            error={!!fieldErrors.medicationName}
            helperText={fieldErrors.medicationName}
          />
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="Dose"
              required
              margin="normal"
              value={dosage}
              onChange={(e) => setDosage(e.target.value)}
              sx={{ flex: 2 }}
              error={!!fieldErrors.dosage}
              helperText={fieldErrors.dosage}
            />
            <TextField
              label="Unidade"
              margin="normal"
              value={dosageUnit}
              onChange={(e) => setDosageUnit(e.target.value)}
              sx={{ flex: 1 }}
            />
          </Box>
          <TextField
            label="Quantidade por administração"
            fullWidth
            required
            margin="normal"
            placeholder="Ex.: 1 comprimido"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            error={!!fieldErrors.quantity}
            helperText={fieldErrors.quantity}
          />
          <TextField
            label="Orientações"
            fullWidth
            multiline
            minRows={2}
            margin="normal"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
          />
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="Data de início"
              type="date"
              required
              margin="normal"
              slotProps={{ inputLabel: { shrink: true } }}
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              sx={{ flex: 1 }}
              error={!!fieldErrors.startDate}
              helperText={fieldErrors.startDate}
            />
            <TextField
              label="Data de término (opcional)"
              type="date"
              margin="normal"
              slotProps={{ inputLabel: { shrink: true } }}
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              sx={{ flex: 1 }}
            />
          </Box>

          <TextField
            select
            label="Recorrência"
            fullWidth
            margin="normal"
            value={recurrenceType}
            onChange={(e) => setRecurrenceType(e.target.value as ScheduleRecurrence)}
          >
            <MenuItem value="daily">Diariamente</MenuItem>
            <MenuItem value="weekly">Dias específicos da semana</MenuItem>
            <MenuItem value="interval">Intervalo em horas</MenuItem>
          </TextField>

          {recurrenceType === "interval" ? (
            <TextField
              label="Intervalo (horas)"
              type="number"
              fullWidth
              margin="normal"
              value={intervalHours}
              onChange={(e) => setIntervalHours(e.target.value)}
            />
          ) : (
            <TextField
              label="Horário"
              type="time"
              fullWidth
              margin="normal"
              slotProps={{ inputLabel: { shrink: true } }}
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
            />
          )}

          <Button type="submit" variant="contained" size="large" sx={{ mt: 2 }} disabled={submitting}>
            Salvar rascunho
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
