import React from 'react';
import { Box, Typography, Button, Paper, SxProps } from '@mui/material';
import { SvgIconComponent } from '@mui/icons-material';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: SvgIconComponent;
  action?: {
    label: string;
    onClick: () => void;
  };
  sx?: SxProps;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon,
  action,
  sx = {},
}) => {
  return (
    <Paper
      sx={{
        p: 4,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        ...sx,
      }}
    >
      {Icon && (
        <Icon
          sx={{
            fontSize: 64,
            color: 'action.disabled',
            mb: 2,
          }}
        />
      )}
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: action ? 3 : 0 }}
        >
          {description}
        </Typography>
      )}
      {action && (
        <Button
          variant="contained"
          color="primary"
          onClick={action.onClick}
          sx={{ mt: 2 }}
        >
          {action.label}
        </Button>
      )}
    </Paper>
  );
};

export default EmptyState;
