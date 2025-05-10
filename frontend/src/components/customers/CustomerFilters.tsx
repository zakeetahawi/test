import React, { useState } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Button
} from '@mui/material';
import { CustomerFilters as CustomerFiltersType } from '../../types/customer';
import { RestartAlt as ResetIcon } from '@mui/icons-material';

interface CustomerFiltersProps {
  onFilterChange: (filters: CustomerFiltersType) => void;
}

export const CustomerFilters: React.FC<CustomerFiltersProps> = ({ onFilterChange }) => {
  const [filters, setFilters] = useState<CustomerFiltersType>({
    search: '',
    customer_type: '',
    status: '',
    category_id: undefined
  });

  const handleFilterChange = (event: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = event.target;
    if (name) {
      const newFilters = {
        ...filters,
        [name]: value
      };
      setFilters(newFilters);
      onFilterChange(newFilters);
    }
  };

  const handleReset = () => {
    const resetFilters = {
      search: '',
      customer_type: '',
      status: '',
      category_id: undefined
    };
    setFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  return (
    <Box component="form" sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            name="search"
            label="بحث"
            variant="outlined"
            size="small"
            value={filters.search}
            onChange={handleFilterChange}
            placeholder="بحث باسم العميل أو رقم الهاتف..."
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>نوع العميل</InputLabel>
            <Select
              name="customer_type"
              value={filters.customer_type}
              label="نوع العميل"
              onChange={handleFilterChange}
            >
              <MenuItem value="">الكل</MenuItem>
              <MenuItem value="individual">فرد</MenuItem>
              <MenuItem value="company">شركة</MenuItem>
              <MenuItem value="government">حكومي</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>الحالة</InputLabel>
            <Select
              name="status"
              value={filters.status}
              label="الحالة"
              onChange={handleFilterChange}
            >
              <MenuItem value="">الكل</MenuItem>
              <MenuItem value="active">نشط</MenuItem>
              <MenuItem value="inactive">غير نشط</MenuItem>
              <MenuItem value="blocked">محظور</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<ResetIcon />}
            onClick={handleReset}
          >
            إعادة تعيين
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};