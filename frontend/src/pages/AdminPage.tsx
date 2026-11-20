import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { listAuditLogs, listProfessionals, verifyProfessional } from "../api/admin";
import type { AuditLog, Professional } from "../api/types";
import { extractErrorMessage } from "../api/client";

function ProfessionalsPanel() {
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listProfessionals()
      .then(setProfessionals)
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleVerify = async (id: number, status: "verified" | "rejected") => {
    try {
      await verifyProfessional(id, status);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  return (
    <>
      {error && <Alert severity="error">{error}</Alert>}
      <Paper variant="outlined">
        <List aria-label="Solicitações de acesso de profissionais">
          {professionals.map((professional) => (
            <ListItem
              key={professional.id}
              secondaryAction={
                professional.verification_status === "pending" && (
                  <Box sx={{ display: "flex", gap: 1 }}>
                    <Button size="small" variant="contained" onClick={() => handleVerify(professional.id, "verified")}>
                      Aprovar
                    </Button>
                    <Button size="small" color="error" onClick={() => handleVerify(professional.id, "rejected")}>
                      Rejeitar
                    </Button>
                  </Box>
                )
              }
            >
              <ListItemText
                primary={`${professional.full_name} (${professional.role})`}
                secondary={professional.email}
              />
              <Chip
                label={professional.verification_status}
                color={
                  professional.verification_status === "verified"
                    ? "success"
                    : professional.verification_status === "rejected"
                      ? "error"
                      : "warning"
                }
                size="small"
                sx={{ mr: 10 }}
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </>
  );
}

function AuditLogsPanel() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAuditLogs({ limit: 100 })
      .then(setLogs)
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  return (
    <>
      {error && <Alert severity="error">{error}</Alert>}
      <Paper variant="outlined">
        <List aria-label="Trilha de auditoria">
          {logs.map((log) => (
            <ListItem key={log.id} divider>
              <ListItemText
                primary={`${log.action} — ${log.resource_type}${log.resource_id ? ` #${log.resource_id}` : ""}`}
                secondary={`${new Date(log.timestamp).toLocaleString("pt-BR")} · ator: ${log.actor_role} (id ${log.actor_id ?? "—"})`}
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </>
  );
}

export function AdminPage() {
  const [tab, setTab] = useState(0);

  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        Administração
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Solicitações de acesso" />
        <Tab label="Auditoria" />
      </Tabs>
      {tab === 0 && <ProfessionalsPanel />}
      {tab === 1 && <AuditLogsPanel />}
    </>
  );
}
