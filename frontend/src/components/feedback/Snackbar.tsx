import React from 'react';
import { Snackbar as MuiSnackbar } from '@mui/material';
import MuiAlert, { AlertProps } from '@mui/material/Alert';
import { useAppSelector, useAppDispatch } from '../../hooks/redux';
import { hideNotification } from '../../store/slices/uiSlice';

const Alert = React.forwardRef<HTMLDivElement, AlertProps>((props, ref) => (
  <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />
));

export const Snackbar = () => {
  const dispatch = useAppDispatch();
  const { message, type, open } = useAppSelector((state) => state.ui.notification);

  const handleClose = () => {
    dispatch(hideNotification());
  };

  return (
    <MuiSnackbar
      open={open}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
    >
      <Alert onClose={handleClose} severity={type} sx={{ width: '100%' }}>
        {message}
      </Alert>
    </MuiSnackbar>
  );
};