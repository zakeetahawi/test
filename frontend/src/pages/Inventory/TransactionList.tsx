import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Chip,
  Button,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useQuery } from 'react-query';
import { Product, InventoryTransaction } from '@/types/inventory';
import inventoryService from '@/services/inventoryService';

interface Props {
  open: boolean;
  onClose: () => void;
  product: Product;
  onAddTransaction: () => void;
}

const TransactionList: React.FC<Props> = ({ open, onClose, product, onAddTransaction }) => {
  const { t } = useTranslation();

  const { data: transactions, isLoading } = useQuery(
    ['transactions', product.id],
    () => inventoryService.getTransactions(product.id),
    {
      enabled: open,
    }
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {t('inventory.transactions_title', { product: product.name })}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={onAddTransaction}
          >
            {t('inventory.add_transaction')}
          </Button>
        </Box>
      </DialogTitle>
      <DialogContent>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('inventory.transaction_date')}</TableCell>
                <TableCell>{t('inventory.transaction_type')}</TableCell>
                <TableCell align="right">{t('inventory.quantity')}</TableCell>
                <TableCell>{t('inventory.reference')}</TableCell>
                <TableCell>{t('inventory.created_by')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    {t('loading')}
                  </TableCell>
                </TableRow>
              ) : transactions?.map((transaction: InventoryTransaction) => (
                <TableRow key={transaction.id}>
                  <TableCell>
                    {new Date(transaction.date).toLocaleDateString('ar-IL', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={t(`inventory.transaction_type.${transaction.type}`)}
                      color={transaction.type === 'in' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      color={transaction.type === 'in' ? 'success.main' : 'error.main'}
                    >
                      {transaction.type === 'in' ? '+' : '-'}
                      {transaction.quantity} {product.unit}
                    </Typography>
                  </TableCell>
                  <TableCell>{transaction.reference}</TableCell>
                  <TableCell>{transaction.createdBy}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

export default TransactionList;