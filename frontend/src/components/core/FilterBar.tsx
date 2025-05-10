import { FC, useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Collapse,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { LoadingButton } from '@mui/lab';

export interface FilterOption {
  field: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'number';
  options?: { value: string | number; label: string }[];
}

interface FilterBarProps {
  onSearch: (query: string) => void;
  onFilter: (filters: Record<string, any>) => void;
  filterOptions: FilterOption[];
  loading?: boolean;
}

const FilterBar: FC<FilterBarProps> = ({
  onSearch,
  onFilter,
  filterOptions,
  loading = false,
}) => {
  const { t } = useTranslation();
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});

  const handleSearch = () => {
    onSearch(searchQuery);
  };

  const handleFilterChange = (field: string, value: any) => {
    const newFilters = {
      ...filters,
      [field]: value,
    };
    setFilters(newFilters);
  };

  const handleApplyFilters = () => {
    onFilter(filters);
  };

  const handleClearFilters = () => {
    setFilters({});
    onFilter({});
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TextField
          fullWidth
          placeholder={t('search_placeholder')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          InputProps={{
            startAdornment: <SearchIcon sx={{ color: 'action.active', mr: 1 }} />,
          }}
        />
        <LoadingButton
          variant="contained"
          onClick={handleSearch}
          loading={loading}
        >
          {t('search')}
        </LoadingButton>
        <IconButton
          color={showFilters ? 'primary' : 'default'}
          onClick={() => setShowFilters(!showFilters)}
        >
          <FilterIcon />
        </IconButton>
      </Box>

      <Collapse in={showFilters}>
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={2}>
            {filterOptions.map((option) => (
              <Grid item xs={12} sm={6} md={4} key={option.field}>
                {option.type === 'select' ? (
                  <FormControl fullWidth>
                    <InputLabel>{option.label}</InputLabel>
                    <Select
                      value={filters[option.field] || ''}
                      onChange={(e: SelectChangeEvent) =>
                        handleFilterChange(option.field, e.target.value)
                      }
                      label={option.label}
                    >
                      <MenuItem value="">
                        <em>{t('all')}</em>
                      </MenuItem>
                      {option.options?.map((opt) => (
                        <MenuItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                ) : (
                  <TextField
                    fullWidth
                    label={option.label}
                    type={option.type}
                    value={filters[option.field] || ''}
                    onChange={(e) =>
                      handleFilterChange(option.field, e.target.value)
                    }
                  />
                )}
              </Grid>
            ))}
          </Grid>
          <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={handleClearFilters}
              startIcon={<ClearIcon />}
            >
              {t('clear_filters')}
            </Button>
            <LoadingButton
              variant="contained"
              onClick={handleApplyFilters}
              loading={loading}
            >
              {t('apply_filters')}
            </LoadingButton>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default FilterBar;