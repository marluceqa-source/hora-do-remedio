import { createTheme } from "@mui/material/styles";

// Contrastes pensados para WCAG 2.2 AA (texto normal ≥ 4.5:1) — seção 2 do prompt do portal.
export const theme = createTheme({
  palette: {
    primary: { main: "#0B5FA5" },
    secondary: { main: "#1B7A43" },
    error: { main: "#B3261E" },
    background: { default: "#F5F7FA" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600 },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        // Foco visível em todo elemento interativo (WCAG 2.4.7).
        "*:focus-visible": {
          outline: "3px solid #0B5FA5",
          outlineOffset: "2px",
        },
      },
    },
  },
});
