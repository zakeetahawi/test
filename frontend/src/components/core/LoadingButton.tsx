import React from 'react';
import {
  Button,
  ButtonProps,
  CircularProgress,
  styled,
  CircularProgressProps,
} from '@mui/material';

interface LoadingButtonProps extends Omit<ButtonProps, 'disabled'> {
  loading?: boolean;
  spinnerSize?: number;
  spinnerColor?: CircularProgressProps['color'];
  disabled?: boolean;
}

const StyledButton = styled(Button)(({ theme }) => ({
  position: 'relative',
  '& .MuiCircularProgress-root': {
    position: 'absolute',
    left: '50%',
    marginLeft: -12,
    marginTop: -12,
  },
  '& .button-content': {
    visibility: 'visible',
  },
  '&.loading': {
    '& .button-content': {
      visibility: 'hidden',
    },
  },
}));

const LoadingButton: React.FC<LoadingButtonProps> = ({
  children,
  loading = false,
  spinnerSize = 24,
  spinnerColor = 'inherit',
  disabled = false,
  startIcon,
  endIcon,
  ...buttonProps
}) => {
  return (
    <StyledButton
      {...buttonProps}
      disabled={loading || disabled}
      className={loading ? 'loading' : ''}
      startIcon={loading ? undefined : startIcon}
      endIcon={loading ? undefined : endIcon}
    >
      <span className="button-content">{children}</span>
      {loading && <CircularProgress size={spinnerSize} color={spinnerColor} />}
    </StyledButton>
  );
};

// Predefined variants for common use cases
export const SubmitButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="contained"
    color="primary"
    type="submit"
    {...props}
  />
);

export const SaveButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="contained"
    color="primary"
    {...props}
  >
    {props.children || 'حفظ'}
  </LoadingButton>
);

export const DeleteButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="outlined"
    color="error"
    {...props}
  >
    {props.children || 'حذف'}
  </LoadingButton>
);

export const CancelButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="outlined"
    color="inherit"
    {...props}
  >
    {props.children || 'إلغاء'}
  </LoadingButton>
);

export const AddButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="contained"
    color="primary"
    {...props}
  >
    {props.children || 'إضافة'}
  </LoadingButton>
);

export const EditButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="outlined"
    color="primary"
    {...props}
  >
    {props.children || 'تعديل'}
  </LoadingButton>
);

export const ViewButton: React.FC<LoadingButtonProps> = (props) => (
  <LoadingButton
    variant="outlined"
    color="info"
    {...props}
  >
    {props.children || 'عرض'}
  </LoadingButton>
);

export default LoadingButton;
