import { ReactNode } from 'react';
import { AlertColor } from '@mui/material';

export type SnackbarSeverity = AlertColor;

export interface SnackbarMessage {
  id: number;
  message: string;
  severity: SnackbarSeverity;
  autoHideDuration?: number;
}

export interface SnackbarContextType {
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  closeSnackbar: (id?: number) => void;
}

export interface SnackbarProviderProps {
  children: ReactNode;
}
