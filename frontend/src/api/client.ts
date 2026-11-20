import axios from "axios";
import type { ApiErrorBody } from "./types";

// A sessão do profissional é um cookie httpOnly (RF01) — withCredentials é obrigatório
// para o navegador enviar/receber esse cookie em chamadas entre origens diferentes
// (frontend em :5173, API em :8000).
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true,
});

// Nomes em português dos campos mais comuns, para contextualizar erros de validação do
// backend (Pydantic responde em inglês e sem dizer o rótulo visível do campo).
const FIELD_LABELS: Record<string, string> = {
  full_name: "Nome completo",
  email: "E-mail",
  password: "Senha",
  new_password: "Nova senha",
  role: "Papel",
  profession: "Profissão",
  council_number: "Número do conselho",
  council_state: "UF do conselho",
  internal_identifier: "Identificador interno",
  birth_date: "Data de nascimento",
  contact: "Contato",
  medication_name: "Nome do medicamento",
  dosage: "Dose",
  dosage_unit: "Unidade da dose",
  quantity_per_administration: "Quantidade por administração",
  instructions: "Orientações",
  start_date: "Data de início",
  end_date: "Data de término",
  code: "Código",
  token: "Token",
};

function fieldLabel(loc: (string | number)[]): string {
  const field = [...loc].reverse().find((part) => typeof part === "string" && part !== "body");
  if (typeof field !== "string") return "Campo";
  return FIELD_LABELS[field] ?? field;
}

function translateValidationError(item: { msg: string; loc: (string | number)[] }): string {
  const label = fieldLabel(item.loc);
  const msg = item.msg;

  const tooShort = msg.match(/at least (\d+) character/i);
  if (tooShort) return `${label}: deve ter pelo menos ${tooShort[1]} caracteres`;

  const tooLong = msg.match(/at most (\d+) character/i);
  if (tooLong) return `${label}: deve ter no máximo ${tooLong[1]} caracteres`;

  if (/field required|missing/i.test(msg)) return `${label}: campo obrigatório`;
  if (/valid email/i.test(msg)) return `${label}: informe um e-mail válido`;
  if (/valid integer|valid number/i.test(msg)) return `${label}: informe um número válido`;
  if (/valid date/i.test(msg)) return `${label}: informe uma data válida`;

  // Mensagens de negócio (ex.: de @model_validator) já vêm legíveis — não prefixar duas vezes.
  if (!/^(string|value|input|field)/i.test(msg)) return msg;

  return `${label}: ${msg}`;
}

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map(translateValidationError).join("; ");

    // Sem resposta do servidor (rede, CORS, API fora do ar) — error.message do Axios vem em
    // inglês ("Network Error", "timeout of Xms exceeded" etc.), nunca mostrar isso cru.
    if (!error.response) {
      if (error.code === "ECONNABORTED") return "O servidor demorou para responder. Tente novamente.";
      return "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.";
    }
    if (error.response.status >= 500) return "Erro interno do servidor. Tente novamente em instantes.";
    return "Ocorreu um erro ao processar a solicitação.";
  }
  return "Ocorreu um erro inesperado.";
}
