import React from 'react';
import {
  Button,
  ButtonProps,
  CircularProgress,
  styled,
  SxProps,
  Theme,
} from '@mui/material';

interface LoadingButtonBaseProps {
  loading?: boolean;
  progressSize?: number;
  loadingPosition?: 'start' | 'end' | 'center';
}

export type LoadingButtonProps = LoadingButtonBaseProps & Omit<ButtonProps, keyof LoadingButtonBaseProps>;

// Styled wrapper to properly position the loading spinner
const LoadingWrapper = styled('span', {
  shouldForwardProp: (prop) => prop !== 'position',
})<{ position: LoadingButtonProps['loadingPosition'] }>(({ position }) => ({
  position: 'absolute',
  display: 'flex',
  alignItems: 'center',
  justifyContent: position === 'center' ? 'center' : 'flex-start',
  left: position === 'start' ? 16 : undefined,
  right: position === 'end' ? 16 : undefined,
  width: position === 'center' ? '100%' : 'auto',
}));

const LoadingButton = React.forwardRef<HTMLButtonElement, LoadingButtonProps>(
  ({
    children,
    loading = false,
    disabled = false,
    progressSize = 20,
    loadingPosition = 'start',
    startIcon,
    endIcon,
    sx,
    ...props
  }, ref) => {
    // Adjust padding when loading to accommodate the spinner
    const buttonSx = React.useMemo<SxProps<Theme>>(() => ({
      position: 'relative',
      ...(loading && loadingPosition === 'start' && {
        paddingLeft: `${progressSize + 24}px`,
      }),
      ...(loading && loadingPosition === 'end' && {
        paddingRight: `${progressSize + 24}px`,
      }),
      ...(typeof sx === 'object' ? sx : {}),
    }), [loading, loadingPosition, progressSize, sx]);

    return (
      <Button
        ref={ref}
        disabled={loading || disabled}
        startIcon={!loading && loadingPosition !== 'center' ? startIcon : undefined}
        endIcon={!loading && loadingPosition !== 'center' ? endIcon : undefined}
        sx={buttonSx}
        {...props}
      >
        {loading && (
          <LoadingWrapper position={loadingPosition}>
            <CircularProgress
              size={progressSize}
              color="inherit"
              sx={{
                opacity: 0.8,
                ...(loadingPosition === 'center' && {
                  position: 'absolute',
                }),
              }}
            />
          </LoadingWrapper>
        )}
        {loading && loadingPosition === 'center' ? (
          <span style={{ visibility: 'hidden' }}>{children}</span>
        ) : (
          children
        )}
      </Button>
    );
  }
);

LoadingButton.displayName = 'LoadingButton';

export default LoadingButton;
