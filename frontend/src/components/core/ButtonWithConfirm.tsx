import { FC, useState } from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  ButtonProps,
} from '@mui/material';
import { useTranslation } from 'react-i18next';

interface ButtonWithConfirmProps extends Omit<ButtonProps, 'onClick'> {
  onConfirm: () => void | Promise<void>;
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
}

const ButtonWithConfirm: FC<ButtonWithConfirmProps> = ({
  onConfirm,
  title,
  description,
  confirmText,
  cancelText,
  children,
  ...buttonProps
}) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    if (!loading) {
      setOpen(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm();
      setOpen(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button {...buttonProps} onClick={handleOpen}>
        {children}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
      >
        <DialogTitle id="confirm-dialog-title">
          {title || t('confirm_action')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="confirm-dialog-description">
            {description || t('confirm_action_description')}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleClose}
            disabled={loading}
            color="inherit"
          >
            {cancelText || t('cancel')}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={loading}
            color="primary"
            autoFocus
          >
            {confirmText || t('confirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ButtonWithConfirm;