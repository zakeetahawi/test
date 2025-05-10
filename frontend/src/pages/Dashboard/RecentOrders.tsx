import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Typography
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { RecentOrder } from '@/services/dashboardService';

interface Props {
  orders: RecentOrder[];
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'info';
    case 'pending':
      return 'warning';
    case 'cancelled':
      return 'error';
    default:
      return 'default';
  }
};

const RecentOrders: React.FC<Props> = ({ orders }) => {
  const { t } = useTranslation();

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{t('orders.id')}</TableCell>
            <TableCell>{t('orders.customer')}</TableCell>
            <TableCell align="right">{t('orders.amount')}</TableCell>
            <TableCell>{t('orders.status')}</TableCell>
            <TableCell>{t('orders.date')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {orders.map((order) => (
            <TableRow key={order.id}>
              <TableCell>#{order.id}</TableCell>
              <TableCell>
                <Typography variant="body2">{order.customerName}</Typography>
              </TableCell>
              <TableCell align="right">
                ₪{order.amount.toLocaleString()}
              </TableCell>
              <TableCell>
                <Chip
                  label={t(`orders.status.${order.status}`)}
                  color={getStatusColor(order.status) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="textSecondary">
                  {new Date(order.date).toLocaleDateString('ar-IL')}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default RecentOrders;