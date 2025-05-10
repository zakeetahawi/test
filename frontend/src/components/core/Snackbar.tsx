import React from 'react';
import {
  Snackbar as MuiSnackbar,
  Alert,
  AlertTitle,
  Typography,
  IconButton,
  Box,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { createContext, useContext, useState } from 'react';

type SnackbarType = 'success' | 'error' | 'warning' | 'info';

interface SnackbarMessage {
  type: SnackbarType;
  message: string;
  title?: string;
  duration?: number;
}

interface SnackbarContextType {
  showSnackbar: (params: SnackbarMessage) => void;
  hideSnackbar: () => void;
}

const SnackbarContext = createContext<SnackbarContextType | undefined>(undefined);

export const useSnackbar = () => {
  const context = useContext(SnackbarContext);
  if (!context) {
    throw new Error('useSnackbar must be used within a SnackbarProvider');
  }
  return context;
};

interface SnackbarProviderProps {
  children: React.ReactNode;
}

export const SnackbarProvider: React.FC<SnackbarProviderProps> = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState<string>('');
  const [title, setTitle] = useState<string | undefined>();
  const [type, setType] = useState<SnackbarType>('info');
  const [duration, setDuration] = useState<number>(6000);

  const showSnackbar = ({ type, message, title, duration = 6000 }: SnackbarMessage) => {
    setType(type);
    setMessage(message);
    setTitle(title);
    setDuration(duration);
    setOpen(true);
  };

  const hideSnackbar = () => {
    setOpen(false);
  };

  const value = {
    showSnackbar,
    hideSnackbar,
  };

  return (
    <SnackbarContext.Provider value={value}>
      {children}
      <MuiSnackbar
        open={open}
        autoHideDuration={duration}
        onClose={hideSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert
          severity={type}
          onClose={hideSnackbar}
          sx={{
            minWidth: '300px',
            '& .MuiAlert-message': {
              width: '100%',
            },
          }}
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={hideSnackbar}
            >
              <CloseIcon fontSize="inherit" />
            </IconButton>
          }
        >
          {title && <AlertTitle>{title}</AlertTitle>}
          <Typography>{message}</Typography>
        </Alert>
      </MuiSnackbar>
    </SnackbarContext.Provider>
  );
};

// Helper functions for common notifications
export const useNotifications = () => {
  const { showSnackbar } = useSnackbar();

  return {
    showSuccess: (message: string, title?: string) =>
      showSnackbar({ type: 'success', message, title }),
    
    showError: (message: string, title?: string) =>
      showSnackbar({ type: 'error', message, title }),
    
    showWarning: (message: string, title?: string) =>
      showSnackbar({ type: 'warning', message, title }),
    
    showInfo: (message: string, title?: string) =>
      showSnackbar({ type: 'info', message, title }),
    
    // Common notification messages
    showSaved: () =>
      showSnackbar({
        type: 'success',
        message: 'تم الحفظ بنجاح',
      }),

    showDeleted: () =>
      showSnackbar({
        type: 'success',
        message: 'تم الحذف بنجاح',
      }),

    showUpdated: () =>
      showSnackbar({
        type: 'success',
        message: 'تم التحديث بنجاح',
      }),

    showCreated: () =>
      showSnackbar({
        type: 'success',
        message: 'تم الإنشاء بنجاح',
      }),

    showApiError: (error: any) =>
      showSnackbar({
        type: 'error',
        title: 'خطأ',
        message: error?.message || 'حدث خطأ غير متوقع',
      }),
  };
};

export type { SnackbarMessage, SnackbarType };
