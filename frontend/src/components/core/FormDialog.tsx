import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Typography,
  Box,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { FormField } from '../../types/common';

interface FormDialogProps {
  open: boolean;
  title: string;
  onClose: () => void;
  onSubmit: () => void;
  loading?: boolean;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  submitLabel?: string;
  cancelLabel?: string;
  showCloseButton?: boolean;
  disableSubmit?: boolean;
  children: React.ReactNode;
}

const FormDialog: React.FC<FormDialogProps> = ({
  open,
  title,
  onClose,
  onSubmit,
  loading = false,
  maxWidth = 'sm',
  submitLabel = 'حفظ',
  cancelLabel = 'إلغاء',
  showCloseButton = true,
  disableSubmit = false,
  children,
}) => {
  const theme = useTheme();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onClose}
      maxWidth={maxWidth}
      fullWidth
      PaperProps={{
        component: 'form',
        onSubmit: handleSubmit,
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">{title}</Typography>
          {showCloseButton && (
            <IconButton
              aria-label="close"
              onClick={onClose}
              disabled={loading}
              size="small"
              sx={{
                color: theme.palette.grey[500],
                '&:hover': {
                  color: theme.palette.grey[700],
                },
              }}
            >
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </DialogTitle>

      <DialogContent dividers>{children}</DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} disabled={loading} color="inherit">
          {cancelLabel}
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={loading || disableSubmit}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : undefined}
        >
          {submitLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Form Row Component
interface FormRowProps {
  children: React.ReactNode;
  spacing?: number;
}

export const FormRow: React.FC<FormRowProps> = ({ children, spacing = 2 }) => (
  <Box
    sx={{
      display: 'flex',
      flexWrap: 'wrap',
      mb: spacing,
      gap: spacing,
      '& > *': {
        flex: 1,
        minWidth: {
          xs: '100%',
          sm: `calc(50% - ${spacing * 4}px)`,
        },
      },
    }}
  >
    {children}
  </Box>
);

// FormSection Component
interface FormSectionProps {
  title?: string;
  children: React.ReactNode;
  noDivider?: boolean;
}

export const FormSection: React.FC<FormSectionProps> = ({ title, children, noDivider }) => (
  <Box sx={{ mb: 3 }}>
    {title && (
      <Typography
        variant="subtitle1"
        sx={{
          mb: 2,
          fontWeight: 500,
          color: 'text.primary',
        }}
      >
        {title}
      </Typography>
    )}
    {children}
    {!noDivider && <Box sx={{ mt: 3, borderBottom: 1, borderColor: 'divider' }} />}
  </Box>
);

export default FormDialog;
