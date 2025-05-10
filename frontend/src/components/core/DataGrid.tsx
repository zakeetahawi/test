import { FC, useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  TableSortLabel,
  Box,
  Checkbox,
  IconButton,
  Typography,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface Column<T> {
  id: keyof T;
  label: string;
  minWidth?: number;
  align?: 'right' | 'left' | 'center';
  format?: (value: any) => string;
  sortable?: boolean;
  filterable?: boolean;
}

interface DataGridProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowId: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  selectable?: boolean;
  onSelectionChange?: (selectedIds: (string | number)[]) => void;
  loading?: boolean;
  emptyMessage?: string;
}

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  if (b[orderBy] < a[orderBy]) return -1;
  if (b[orderBy] > a[orderBy]) return 1;
  return 0;
}

function getComparator<T>(
  order: 'asc' | 'desc',
  orderBy: keyof T
): (a: T, b: T) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

const DataGrid = <T extends object>({
  columns,
  rows,
  getRowId,
  onRowClick,
  selectable = false,
  onSelectionChange,
  loading = false,
  emptyMessage,
}: DataGridProps<T>) => {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState<keyof T | null>(null);
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');
  const [selected, setSelected] = useState<(string | number)[]>([]);
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState<{ [key in keyof T]?: string }>({});

  const handleSort = (property: keyof T) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = rows.map((row) => getRowId(row));
      setSelected(newSelected);
      onSelectionChange?.(newSelected);
    } else {
      setSelected([]);
      onSelectionChange?.([]);
    }
  };

  const handleRowSelect = (id: string | number) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: (string | number)[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }

    setSelected(newSelected);
    onSelectionChange?.(newSelected);
  };

  const handleSearch = (text: string) => {
    setSearchText(text);
    setPage(0);
  };

  const handleFilter = (column: keyof T, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [column]: value,
    }));
    setPage(0);
  };

  // تطبيق الفلترة والبحث والترتيب
  let filteredRows = [...rows];

  // تطبيق البحث
  if (searchText) {
    filteredRows = filteredRows.filter((row) =>
      Object.values(row).some(
        (value) =>
          value &&
          value.toString().toLowerCase().includes(searchText.toLowerCase())
      )
    );
  }

  // تطبيق الفلاتر
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      filteredRows = filteredRows.filter((row) => {
        const cellValue = row[key as keyof T];
        return (
          cellValue &&
          cellValue.toString().toLowerCase().includes(value.toLowerCase())
        );
      });
    }
  });

  // تطبيق الترتيب
  if (orderBy) {
    filteredRows.sort(getComparator(order, orderBy));
  }

  // تطبيق الصفحات
  const paginatedRows = filteredRows.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const isRowSelected = (id: string | number) => selected.indexOf(id) !== -1;

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <TextField
          size="small"
          placeholder={t('search')}
          value={searchText}
          onChange={(e) => handleSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <TableContainer>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {selectable && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={
                      selected.length > 0 && selected.length < rows.length
                    }
                    checked={
                      rows.length > 0 && selected.length === rows.length
                    }
                    onChange={handleSelectAllClick}
                  />
                </TableCell>
              )}
              {columns.map((column) => (
                <TableCell
                  key={column.id.toString()}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {column.sortable ? (
                      <TableSortLabel
                        active={orderBy === column.id}
                        direction={
                          orderBy === column.id ? order : 'asc'
                        }
                        onClick={() => handleSort(column.id)}
                      >
                        {column.label}
                      </TableSortLabel>
                    ) : (
                      column.label
                    )}
                    {column.filterable && (
                      <IconButton
                        size="small"
                        onClick={() =>
                          handleFilter(
                            column.id,
                            filters[column.id] ? '' : ' '
                          )
                        }
                      >
                        <FilterIcon />
                      </IconButton>
                    )}
                  </Box>
                  {column.filterable && filters[column.id] && (
                    <TextField
                      size="small"
                      fullWidth
                      value={filters[column.id]}
                      onChange={(e) =>
                        handleFilter(column.id, e.target.value)
                      }
                      sx={{ mt: 1 }}
                    />
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={
                    columns.length + (selectable ? 1 : 0)
                  }
                  align="center"
                >
                  <Typography>{t('loading')}</Typography>
                </TableCell>
              </TableRow>
            ) : paginatedRows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={
                    columns.length + (selectable ? 1 : 0)
                  }
                  align="center"
                >
                  <Typography>
                    {emptyMessage || t('no_data')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedRows.map((row) => {
                const id = getRowId(row);
                const isItemSelected = isRowSelected(id);

                return (
                  <TableRow
                    hover
                    onClick={(event) => {
                      if (selectable) {
                        handleRowSelect(id);
                      }
                      onRowClick?.(row);
                    }}
                    role="checkbox"
                    aria-checked={isItemSelected}
                    tabIndex={-1}
                    key={id}
                    selected={isItemSelected}
                    sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                  >
                    {selectable && (
                      <TableCell padding="checkbox">
                        <Checkbox checked={isItemSelected} />
                      </TableCell>
                    )}
                    {columns.map((column) => {
                      const value = row[column.id];
                      return (
                        <TableCell
                          key={column.id.toString()}
                          align={column.align}
                        >
                          {column.format
                            ? column.format(value)
                            : value}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={filteredRows.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10));
          setPage(0);
        }}
      />
    </Paper>
  );
};

export default DataGrid;