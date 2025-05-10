import React from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Collapse,
  IconButton,
  Typography,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

interface DelayInfo {
  stepName: string;
  delayMinutes: number;
  reason?: string;
  severity: 'warning' | 'error';
}

interface Props {
  delay: DelayInfo;
  onClose: () => void;
}

export const InstallationDelayAlert: React.FC<Props> = ({ delay, onClose }) => {
  const [open, setOpen] = React.useState(true);

  const handleClose = () => {
    setOpen(false);
    setTimeout(onClose, 300); // Give time for animation to complete
  };

  const formatDelay = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} دقيقة`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours} ساعة ${remainingMinutes > 0 ? `و ${remainingMinutes} دقيقة` : ''}`;
  };

  return (
    <Collapse in={open}>
      <Alert
        severity={delay.severity}
        sx={{
          mb: 2,
          borderRadius: 2,
          '& .MuiAlert-message': {
            width: '100%',
          },
        }}
        action={
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={handleClose}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        }
      >
        <AlertTitle sx={{ fontWeight: 'bold' }}>
          {delay.severity === 'error' ? 'تأخير كبير' : 'تأخير بسيط'} في التركيب
        </AlertTitle>
        <Box>
          <Typography variant="body2" gutterBottom>
            تم تسجيل تأخير في خطوة <strong>{delay.stepName}</strong> لمدة{' '}
            <strong>{formatDelay(delay.delayMinutes)}</strong>
          </Typography>
          {delay.reason && (
            <Typography variant="body2" color="text.secondary">
              السبب: {delay.reason}
            </Typography>
          )}
        </Box>
      </Alert>
    </Collapse>
  );
};