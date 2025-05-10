import React from 'react';
import { Card, CardHeader, CardContent, IconButton } from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';

interface DashboardCardProps {
  title: string;
  children: React.ReactNode;
  height?: number | string;
  action?: React.ReactNode;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  children,
  height = 'auto',
  action,
}) => {
  return (
    <Card sx={{ height }}>
      <CardHeader
        title={title}
        action={
          action || (
            <IconButton aria-label="settings">
              <MoreVertIcon />
            </IconButton>
          )
        }
      />
      <CardContent sx={{ height: 'calc(100% - 76px)', overflow: 'auto' }}>
        {children}
      </CardContent>
    </Card>
  );
};

export default DashboardCard;