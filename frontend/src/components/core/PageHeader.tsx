import React from 'react';
import {
  Box,
  Typography,
  Button,
  Breadcrumbs,
  Link as MuiLink,
  Stack,
  Paper,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';

interface Breadcrumb {
  label: string;
  link?: string;
}

interface Action {
  label: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  to?: string;
  variant?: 'text' | 'outlined' | 'contained';
  color?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Breadcrumb[];
  actions?: Action[];
  showDivider?: boolean;
  className?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  actions,
  showDivider = true,
  className,
}) => {
  const theme = useTheme();

  const renderBreadcrumbs = () => {
    if (!breadcrumbs?.length) return null;

    return (
      <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 1 }}>
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;

          if (isLast || !crumb.link) {
            return (
              <Typography
                key={index}
                color="text.primary"
                sx={{ fontSize: '0.875rem' }}
              >
                {crumb.label}
              </Typography>
            );
          }

          return (
            <MuiLink
              key={index}
              component={RouterLink}
              to={crumb.link}
              color="inherit"
              sx={{
                fontSize: '0.875rem',
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                },
              }}
            >
              {crumb.label}
            </MuiLink>
          );
        })}
      </Breadcrumbs>
    );
  };

  const renderActions = () => {
    if (!actions?.length) return null;

    return (
      <Stack direction="row" spacing={1}>
        {actions.map((action, index) => {
          const ButtonComponent = action.to ? RouterLink : Button;
          const buttonProps = action.to
            ? { to: action.to, component: RouterLink }
            : { onClick: action.onClick };

          return (
            <Button
              key={index}
              variant={action.variant || 'contained'}
              color={action.color || 'primary'}
              startIcon={action.icon}
              {...buttonProps}
            >
              {action.label}
            </Button>
          );
        })}
      </Stack>
    );
  };

  return (
    <Paper
      className={className}
      sx={{
        mb: 3,
        p: 3,
        borderRadius: theme.shape.borderRadius,
        backgroundColor: 'background.paper',
      }}
      elevation={0}
    >
      {renderBreadcrumbs()}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" gutterBottom={Boolean(subtitle)}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="subtitle1" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        {renderActions()}
      </Box>
      {showDivider && <Box sx={{ mt: 3, borderBottom: 1, borderColor: 'divider' }} />}
    </Paper>
  );
};

export type { Breadcrumb, Action };
export default PageHeader;
