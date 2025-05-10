import React from 'react';
import { Chip, ChipProps } from '@mui/material';
import { styled } from '@mui/material/styles';

type StatusType =
  | 'active'
  | 'inactive'
  | 'pending'
  | 'processing'
  | 'completed'
  | 'cancelled'
  | 'blocked'
  | 'scheduled'
  | 'in_progress'
  | 'unpaid'
  | 'partially_paid'
  | 'paid'
  | 'out_of_stock';

interface StatusConfig {
  label: string;
  color: ChipProps['color'];
  variant?: ChipProps['variant'];
}

const statusConfigs: Record<StatusType, StatusConfig> = {
  // Common statuses
  active: { label: 'نشط', color: 'success' },
  inactive: { label: 'غير نشط', color: 'default' },
  blocked: { label: 'محظور', color: 'error' },

  // Order statuses
  pending: { label: 'قيد الانتظار', color: 'warning' },
  processing: { label: 'قيد المعالجة', color: 'info' },
  completed: { label: 'مكتمل', color: 'success' },
  cancelled: { label: 'ملغي', color: 'error' },

  // Installation/Inspection statuses
  scheduled: { label: 'مجدول', color: 'info' },
  in_progress: { label: 'قيد التنفيذ', color: 'warning' },

  // Payment statuses
  unpaid: { label: 'غير مدفوع', color: 'error' },
  partially_paid: { label: 'مدفوع جزئياً', color: 'warning' },
  paid: { label: 'مدفوع', color: 'success' },

  // Inventory status
  out_of_stock: { label: 'نفذ من المخزون', color: 'error' },
};

const StyledChip = styled(Chip)(({ theme }) => ({
  fontWeight: 500,
  fontSize: '0.875rem',
  '&.MuiChip-filledSuccess': {
    backgroundColor: theme.palette.success.main,
    color: theme.palette.success.contrastText,
  },
  '&.MuiChip-filledError': {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
  },
  '&.MuiChip-filledWarning': {
    backgroundColor: theme.palette.warning.main,
    color: theme.palette.warning.contrastText,
  },
  '&.MuiChip-filledInfo': {
    backgroundColor: theme.palette.info.main,
    color: theme.palette.info.contrastText,
  },
  '&.MuiChip-outlinedSuccess': {
    borderColor: theme.palette.success.main,
    color: theme.palette.success.main,
  },
  '&.MuiChip-outlinedError': {
    borderColor: theme.palette.error.main,
    color: theme.palette.error.main,
  },
  '&.MuiChip-outlinedWarning': {
    borderColor: theme.palette.warning.main,
    color: theme.palette.warning.main,
  },
  '&.MuiChip-outlinedInfo': {
    borderColor: theme.palette.info.main,
    color: theme.palette.info.main,
  },
}));

interface StatusLabelProps {
  status: StatusType;
  variant?: ChipProps['variant'];
  size?: ChipProps['size'];
  className?: string;
}

const StatusLabel: React.FC<StatusLabelProps> = ({
  status,
  variant = 'filled',
  size = 'small',
  className,
}) => {
  const config = statusConfigs[status];

  if (!config) {
    console.warn(`Unknown status: ${status}`);
    return null;
  }

  return (
    <StyledChip
      label={config.label}
      color={config.color}
      variant={variant}
      size={size}
      className={className}
    />
  );
};

export type { StatusType };
export default StatusLabel;
