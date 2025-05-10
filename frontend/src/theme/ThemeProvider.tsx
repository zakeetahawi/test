import React from 'react';
import { ThemeProvider as MUIThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme, getThemeByName } from './theme';
import RTL from './RTL';

interface ThemeContextType {
  currentTheme: string;
  setTheme: (name: string) => void;
}

export const ThemeContext = React.createContext<ThemeContextType>({
  currentTheme: 'default',
  setTheme: () => {},
});

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [currentTheme, setCurrentTheme] = React.useState<string>(() => {
    try {
      return localStorage.getItem('selectedTheme') || 'default';
    } catch {
      return 'default';
    }
  });

  const setTheme = React.useCallback((name: string) => {
    try {
      setCurrentTheme(name);
      localStorage.setItem('selectedTheme', name);
    } catch (error) {
      console.error('Failed to set theme:', error);
    }
  }, []);

  const themeValue = React.useMemo(() => ({
    currentTheme,
    setTheme,
  }), [currentTheme, setTheme]);

  const activeTheme = React.useMemo(() => {
    try {
      return currentTheme === 'default' ? theme : getThemeByName(currentTheme);
    } catch (error) {
      console.error('Failed to get theme:', error);
      return theme;
    }
  }, [currentTheme]);

  return (
    <ThemeContext.Provider value={themeValue}>
      <MUIThemeProvider theme={activeTheme}>
        <CssBaseline />
        <RTL>{children}</RTL>
      </MUIThemeProvider>
    </ThemeContext.Provider>
  );
};
