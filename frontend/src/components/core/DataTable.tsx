import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Box,
  CircularProgress,
  Typography,
  IconButton,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface Column {
  id: string;
  label: string;
  minWidth?: number;
  align?: 'left' | 'right' | 'center';
  format?: (value: any) => string | JSX.Element;
  sortable?: boolean;
}

interface DataTableProps {
  columns: Column[];
  data: any[];
  totalCount: number;
  page: number;
  pageSize: number;
  loading?: boolean;
  error?: string;
  orderBy?: string;
  orderDirection?: 'asc' | 'desc';
  searchable?: boolean;
  searchText?: string;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newPageSize: number) => void;
  onSearchChange?: (searchText: string) => void;
  onSortChange?: (orderBy: string, orderDirection: 'asc' | 'desc') => void;
  emptyMessage?: string;
  rowsPerPageOptions?: number[];
}

const DataTable: React.FC<DataTableProps> = ({
  columns,
  data,
  totalCount,
  page,
  pageSize,
  loading = false,
  error,
  orderBy,
  orderDirection = 'asc',
  searchable = true,
  searchText = '',
  onPageChange,
  onPageSizeChange,
  onSearchChange,
  onSortChange,
  emptyMessage = 'لا توجد بيانات للعرض',
  rowsPerPageOptions = [10, 25, 50, 100],
}) => {
  const theme = useTheme();
  const [searchValue, setSearchValue] = React.useState(searchText);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setSearchValue(newValue);
    if (onSearchChange) {
      onSearchChange(newValue);
    }
  };

  const handleSort = (columnId: string) => {
    if (!onSortChange) return;

    const isAsc = orderBy === columnId && orderDirection === 'asc';
    onSortChange(columnId, isAsc ? 'desc' : 'asc');
  };

  const renderSortIcon = (column: Column) => {
    if (!column.sortable) return null;
    if (orderBy !== column.id) return null;

    return orderDirection === 'asc' ? (
      <KeyboardArrowUpIcon fontSize="small" />
    ) : (
      <KeyboardArrowDownIcon fontSize="small" />
    );
  };

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      {searchable && (
        <Box sx={{ p: 2 }}>
          <TextField
            fullWidth
            placeholder="بحث..."
            value={searchValue}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>
      )}

      <TableContainer sx={{ maxHeight: '70vh' }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                  sortDirection={orderBy === column.id ? orderDirection : false}
                >
                  {column.sortable ? (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                      }}
                      onClick={() => handleSort(column.id)}
                    >
                      {column.label}
                      {renderSortIcon(column)}
                    </Box>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center" sx={{ py: 5 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center" sx={{ py: 5 }}>
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, index) => (
                <TableRow hover tabIndex={-1} key={index}>
                  {columns.map((column) => {
                    const value = row[column.id];
                    return (
                      <TableCell key={column.id} align={column.align}>
                        {column.format ? column.format(value) : value}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={totalCount}
        rowsPerPage={pageSize}
        page={page}
        rowsPerPageOptions={rowsPerPageOptions}
        onPageChange={(_, newPage) => onPageChange(newPage)}
        onRowsPerPageChange={(event) =>
          onPageSizeChange(parseInt(event.target.value, 10))
        }
        labelRowsPerPage="عدد العناصر في الصفحة:"
        labelDisplayedRows={({ from, to, count }) =>
          `${from}-${to} من ${count !== -1 ? count : `أكثر من ${to}`}`
        }
      />
    </Paper>
  );
};

export default DataTable;
