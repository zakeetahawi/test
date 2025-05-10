import React, { createContext, useContext, useState } from 'react';
import { Snackbar, Alert } from '@mui/material';
import type { SnackbarContextType, SnackbarMessage, SnackbarProviderProps } from './types';

const SnackbarContext = createContext<SnackbarContextType | null>(null);

let snackbarId = 0;

export const SnackbarProvider: React.FC<SnackbarProviderProps> = ({ children }) => {
  const [snackbars, setSnackbars] = useState<SnackbarMessage[]>([]);

  const showMessage = (message: string, severity: SnackbarMessage['severity'], duration = 6000) => {
    const id = snackbarId++;
    setSnackbars(prev => [...prev, { id, message, severity, autoHideDuration: duration }]);
  };

  const closeSnackbar = (id?: number) => {
    setSnackbars(prev => prev.filter(snackbar => snackbar.id !== id));
  };

  const showSuccess = (message: string, duration?: number) => {
    showMessage(message, 'success', duration);
  };

  const showError = (message: string, duration?: number) => {
    showMessage(message, 'error', duration);
  };

  const showInfo = (message: string, duration?: number) => {
    showMessage(message, 'info', duration);
  };

  const showWarning = (message: string, duration?: number) => {
    showMessage(message, 'warning', duration);
  };

  const contextValue: SnackbarContextType = {
    showSuccess,
    showError,
    showInfo,
    showWarning,
    closeSnackbar,
  };

  return (
    <SnackbarContext.Provider value={contextValue}>
      {children}
      {snackbars.map(({ id, message, severity, autoHideDuration }) => (
        <Snackbar
          key={id}
          open={true}
          autoHideDuration={autoHideDuration}
          onClose={() => closeSnackbar(id)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
          sx={{ direction: 'rtl' }}
        >
          <Alert
            onClose={() => closeSnackbar(id)}
            severity={severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {message}
          </Alert>
        </Snackbar>
      ))}
    </SnackbarContext.Provider>
  );
};

export const useSnackbar = () => {
  const context = useContext(SnackbarContext);
  if (!context) {
    throw new Error('useSnackbar must be used within a SnackbarProvider');
  }
  return context;
};

export default SnackbarContext;
