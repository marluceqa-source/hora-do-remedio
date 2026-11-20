import { useEffect, useState } from "react";
import { Alert, Card, CardContent, Grid, Typography } from "@mui/material";
import { getDashboard } from "../api/dashboard";
import type { Dashboard } from "../api/types";
import { extractErrorMessage } from "../api/client";

function StatCard({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <Grid size={{ xs: 12, sm: 6, md: 3 }}>
      <Card variant="outlined" sx={{ height: "100%" }}>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="h3" component="p">
            {value}
          </Typography>
          {hint && (
            <Typography variant="caption" color="text.secondary">
              {hint}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Grid>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {data && (
        <Grid container spacing={2}>
          <StatCard label="Pacientes vinculados" value={data.total_patients} />
          <StatCard label="Tratamentos ativos" value={data.active_treatments} />
          <StatCard
            label="Terminando em breve"
            value={data.treatments_ending_soon}
            hint="Próximos 7 dias"
          />
          <StatCard label="Lembretes enviados" value={data.reminders_sent} />
          <StatCard label="Doses confirmadas" value={data.doses_confirmed} />
          <StatCard label="Doses não tomadas" value={data.doses_not_taken} hint="Declarado pelo paciente" />
          <StatCard
            label="Sem confirmação"
            value={data.doses_unconfirmed}
            hint="Não significa que não foi tomado (RN12)"
          />
        </Grid>
      )}
    </>
  );
}
