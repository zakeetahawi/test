import { createTheme } from '@mui/material/styles';

const defaultTheme = {
  primary: '#8B735A',
  secondary: '#A67B5B',
  accent: '#5F4B32',
  neutral: '#B7A99A',
  lightBg: '#E8DCCA',
  darkText: '#3D3427',
  alert: '#C17817',
  lightAccent: '#D2B48C',
};

export const theme = createTheme({
  direction: 'rtl',
  palette: {
    primary: {
      main: defaultTheme.primary,
      light: defaultTheme.lightAccent,
      dark: defaultTheme.accent,
    },
    secondary: {
      main: defaultTheme.secondary,
      light: defaultTheme.lightBg,
      dark: defaultTheme.darkText,
    },
    error: {
      main: defaultTheme.alert,
    },
    background: {
      default: defaultTheme.lightBg,
      paper: '#fff',
    },
    text: {
      primary: defaultTheme.darkText,
      secondary: defaultTheme.neutral,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: defaultTheme.lightBg,
          color: defaultTheme.darkText,
        },
      },
    },
  },
});

// Theme colors for different themes
const themes = {
  'light-sky': {
    primary: '#7FB3D5',
    secondary: '#85C1E9',
    accent: '#3498DB',
    neutral: '#BDC3C7',
    lightBg: '#EBF5FB',
    darkText: '#2C3E50',
    alert: '#E74C3C',
    lightAccent: '#AED6F1',
  },
  'soft-pink': {
    primary: '#F1948A',
    secondary: '#F5B7B1',
    accent: '#E74C3C',
    neutral: '#FADBD8',
    lightBg: '#FDEDEC',
    darkText: '#943126',
    alert: '#C0392B',
    lightAccent: '#F2D7D5',
  },
  // Add other themes here...
};

export function getThemeByName(name: string) {
  const themeColors = themes[name] || defaultTheme;
  return createTheme({
    ...theme,
    palette: {
      ...theme.palette,
      primary: {
        main: themeColors.primary,
        light: themeColors.lightAccent,
        dark: themeColors.accent,
      },
      secondary: {
        main: themeColors.secondary,
        light: themeColors.lightBg,
        dark: themeColors.darkText,
      },
      error: {
        main: themeColors.alert,
      },
      background: {
        default: themeColors.lightBg,
        paper: '#fff',
      },
      text: {
        primary: themeColors.darkText,
        secondary: themeColors.neutral,
      },
    },
  });
}