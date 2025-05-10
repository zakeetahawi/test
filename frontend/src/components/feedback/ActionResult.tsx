import React from 'react';
import { Alert, AlertTitle, Box, Collapse } from '@mui/material';

interface ActionResultProps {
  success?: boolean;
  message: string;
  title?: string;
  show: boolean;
  onClose?: () => void;
}

export const ActionResult: React.FC<ActionResultProps> = ({
  success = true,
  message,
  title,
  show,
  onClose
}) => {
  return (
    <Box sx={{ position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 9999, width: '90%', maxWidth: 500 }}>
      <Collapse in={show}>
        <Alert 
          severity={success ? "success" : "error"}
          onClose={onClose}
          sx={{ 
            boxShadow: 3,
            '& .MuiAlert-message': {
              width: '100%'
            }
          }}
        >
          {title && <AlertTitle>{title}</AlertTitle>}
          {message}
        </Alert>
      </Collapse>
    </Box>
  );
};