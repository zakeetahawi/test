import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box,
  IconButton,
  useTheme,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Help as HelpIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import LoadingButton, { CancelButton } from './LoadingButton';

type ConfirmType = 'warning' | 'error' | 'info' | 'confirm';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string | React.ReactNode;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  type?: ConfirmType;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  showCloseButton?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  onConfirm,
  onCancel,
  type = 'confirm',
  confirmLabel,
  cancelLabel = 'إلغاء',
  loading = false,
  maxWidth = 'xs',
  showCloseButton = true,
}) => {
  const theme = useTheme();

  const getIcon = () => {
    const iconProps = {
      sx: {
        fontSize: 40,
        color: getIconColor(),
      },
    };

    switch (type) {
      case 'warning':
        return <WarningIcon {...iconProps} />;
      case 'error':
        return <ErrorIcon {...iconProps} />;
      case 'info':
        return <InfoIcon {...iconProps} />;
      default:
        return <HelpIcon {...iconProps} />;
    }
  };

  const getIconColor = () => {
    switch (type) {
      case 'warning':
        return theme.palette.warning.main;
      case 'error':
        return theme.palette.error.main;
      case 'info':
        return theme.palette.info.main;
      default:
        return theme.palette.primary.main;
    }
  };

  const getButtonColor = () => {
    switch (type) {
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'info':
        return 'info';
      default:
        return 'primary';
    }
  };

  const getDefaultConfirmLabel = () => {
    switch (type) {
      case 'warning':
        return 'متابعة';
      case 'error':
        return 'حذف';
      case 'info':
        return 'موافق';
      default:
        return 'تأكيد';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onCancel}
      maxWidth={maxWidth}
      fullWidth
      PaperProps={{
        elevation: 0,
        sx: {
          borderRadius: 2,
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getIcon()}
            <Typography variant="h6">{title}</Typography>
          </Box>
          {showCloseButton && (
            <IconButton
              aria-label="close"
              onClick={onCancel}
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

      <DialogContent>
        {typeof message === 'string' ? (
          <Typography>{message}</Typography>
        ) : (
          message
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <CancelButton onClick={onCancel} disabled={loading}>
          {cancelLabel}
        </CancelButton>
        <LoadingButton
          variant="contained"
          color={getButtonColor()}
          onClick={onConfirm}
          loading={loading}
        >
          {confirmLabel || getDefaultConfirmLabel()}
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export type { ConfirmType };
export default ConfirmDialog;
