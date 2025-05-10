import { FC } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import { StockTransaction } from '@services/inventoryService';

interface RecentTransactionsProps {
  transactions: StockTransaction[];
}

const getTransactionTypeColor = (type: string) => {
  switch (type) {
    case 'in':
      return 'success';
    case 'out':
      return 'error';
    case 'transfer':
      return 'info';
    case 'adjustment':
      return 'warning';
    default:
      return 'default';
  }
};

const getTransactionTypeLabel = (type: string) => {
  switch (type) {
    case 'in':
      return 'وارد';
    case 'out':
      return 'صادر';
    case 'transfer':
      return 'نقل';
    case 'adjustment':
      return 'تسوية';
    default:
      return type;
  }
};

const RecentTransactions: FC<RecentTransactionsProps> = ({ transactions }) => {
  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>المنتج</TableCell>
            <TableCell>نوع العملية</TableCell>
            <TableCell>الكمية</TableCell>
            <TableCell>السبب</TableCell>
            <TableCell>التاريخ</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {transactions.map((transaction) => (
            <TableRow key={transaction.id}>
              <TableCell>{transaction.product}</TableCell>
              <TableCell>
                <Chip
                  label={getTransactionTypeLabel(transaction.transaction_type)}
                  color={getTransactionTypeColor(transaction.transaction_type)}
                  size="small"
                />
              </TableCell>
              <TableCell>{transaction.quantity}</TableCell>
              <TableCell>{transaction.reason}</TableCell>
              <TableCell>
                {new Date(transaction.date).toLocaleDateString('ar-SA')}
              </TableCell>
            </TableRow>
          ))}
          {transactions.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} align="center">
                لا توجد معاملات حديثة
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default RecentTransactions;