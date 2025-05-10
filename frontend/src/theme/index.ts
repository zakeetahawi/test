import { createTheme } from '@mui/material/styles';
import { arEG } from '@mui/material/locale';

declare module '@mui/material/styles' {
  interface Palette {
    neutral: Palette['primary'];
    accent: Palette['primary'];
    alert: Palette['primary'];
    lightAccent: Palette['primary'];
  }

  interface PaletteOptions {
    neutral?: PaletteOptions['primary'];
    accent?: PaletteOptions['primary'];
    alert?: PaletteOptions['primary'];
    lightAccent?: PaletteOptions['primary'];
  }
}

const defaultTheme = createTheme({
  direction: 'rtl',
  palette: {
    primary: {
      main: 'var(--primary, #007bff)',
      light: 'var(--primary-light, #3395ff)',
      dark: 'var(--primary-dark, #0056b3)',
      contrastText: '#fff',
    },
    secondary: {
      main: 'var(--secondary, #6c757d)',
      light: 'var(--secondary-light, #868e96)',
      dark: 'var(--secondary-dark, #495057)',
      contrastText: '#fff',
    },
    neutral: {
      main: 'var(--neutral, #e9ecef)',
      light: 'var(--neutral-light, #f8f9fa)',
      dark: 'var(--neutral-dark, #dee2e6)',
      contrastText: '#000',
    },
    accent: {
      main: 'var(--accent, #17a2b8)',
      light: 'var(--accent-light, #1fc8e3)',
      dark: 'var(--accent-dark, #117a8b)',
      contrastText: '#fff',
    },
    lightAccent: {
      main: 'var(--light-accent, #f1f9fb)',
      light: 'var(--light-accent-light, #ffffff)',
      dark: 'var(--light-accent-dark, #e3f3f7)',
      contrastText: '#000',
    },
    alert: {
      main: 'var(--alert, #dc3545)',
      light: 'var(--alert-light, #e4606d)',
      dark: 'var(--alert-dark, #bd2130)',
      contrastText: '#fff',
    },
    error: {
      main: '#dc3545',
      light: '#e4606d',
      dark: '#bd2130',
      contrastText: '#fff',
    },
    warning: {
      main: '#ffc107',
      light: '#ffcd38',
      dark: '#d39e00',
      contrastText: '#000',
    },
    info: {
      main: '#17a2b8',
      light: '#1fc8e3',
      dark: '#117a8b',
      contrastText: '#fff',
    },
    success: {
      main: '#28a745',
      light: '#48c774',
      dark: '#1e7e34',
      contrastText: '#fff',
    },
  },
  typography: {
    fontFamily: '"system-ui", "Segoe UI", "Helvetica Neue", sans-serif',
    fontSize: 14,
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 700,
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#f8f9fa',
          color: '#212529',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '0.25rem',
          padding: '0.375rem 0.75rem',
          fontSize: '1rem',
          lineHeight: 1.5,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '0.25rem',
          boxShadow: '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: '1px solid var(--neutral, #e9ecef)',
          borderRadius: '0.25rem',
        },
      },
    },
    MuiCardHeader: {
      styleOverrides: {
        root: {
          padding: '0.75rem 1.25rem',
          backgroundColor: 'var(--neutral-light, #f8f9fa)',
          borderBottom: '1px solid var(--neutral, #e9ecef)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: 'var(--neutral-light, #f8f9fa)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '0.75rem',
          borderBottom: '1px solid var(--neutral, #e9ecef)',
        },
        head: {
          fontWeight: 600,
          backgroundColor: 'var(--neutral-light, #f8f9fa)',
        },
      },
    },
  },
}, arEG);

const themes = {
  default: defaultTheme,
  'light-sky': createTheme({
    ...defaultTheme,
    palette: {
      ...defaultTheme.palette,
      primary: { main: '#4dabf5' },
      accent: { main: '#2196f3' },
    },
  }),
  'soft-pink': createTheme({
    ...defaultTheme,
    palette: {
      ...defaultTheme.palette,
      primary: { main: '#f48fb1' },
      accent: { main: '#ec407a' },
    },
  }),
  'fresh-mint': createTheme({
    ...defaultTheme,
    palette: {
      ...defaultTheme.palette,
      primary: { main: '#81c784' },
      accent: { main: '#4caf50' },
    },
  }),
  'calm-lavender': createTheme({
    ...defaultTheme,
    palette: {
      ...defaultTheme.palette,
      primary: { main: '#9575cd' },
      accent: { main: '#673ab7' },
    },
  }),
  'warm-beige': createTheme({
    ...defaultTheme,
    palette: {
      ...defaultTheme.palette,
      primary: { main: '#bcaaa4' },
      accent: { main: '#795548' },
    },
  }),
};

export { themes, defaultTheme };
