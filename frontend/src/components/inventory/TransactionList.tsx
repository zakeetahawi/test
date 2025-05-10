import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  TextField,
  IconButton,
  Chip,
} from '@mui/material';
import { Download as DownloadIcon, Search as SearchIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import { ar } from 'date-fns/locale';
import { InventoryTransaction } from '@/types/inventory';

interface Props {
  transactions: InventoryTransaction[];
  onSearch?: (query: string) => void;
  onExport?: () => void;
}

const TransactionList: React.FC<Props> = ({
  transactions,
  onSearch,
  onExport,
}) => {
  const { t } = useTranslation();

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          {t('inventory.transactions')}
        </Typography>

        <Box display="flex" gap={2}>
          <TextField
            size="small"
            placeholder={t('inventory.search_transactions')}
            InputProps={{
              startAdornment: <SearchIcon color="action" />,
            }}
            onChange={(e) => onSearch?.(e.target.value)}
          />

          {onExport && (
            <IconButton onClick={onExport} title={t('inventory.export_transactions')}>
              <DownloadIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('date')}</TableCell>
              <TableCell>{t('inventory.transaction_type')}</TableCell>
              <TableCell align="right">{t('inventory.quantity')}</TableCell>
              <TableCell>{t('inventory.reference')}</TableCell>
              <TableCell>{t('inventory.notes')}</TableCell>
              <TableCell>{t('created_by')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {transactions.map((transaction) => (
              <TableRow key={transaction.id}>
                <TableCell>
                  {format(new Date(transaction.date), 'PPpp', { locale: ar })}
                </TableCell>
                <TableCell>
                  <Chip
                    label={t(`inventory.transaction_type.${transaction.type}`)}
                    color={transaction.type === 'in' ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  {transaction.quantity}
                </TableCell>
                <TableCell>{transaction.reference}</TableCell>
                <TableCell>{transaction.notes || '-'}</TableCell>
                <TableCell>{transaction.createdBy}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default TransactionList;