import { FC, useState, useEffect } from 'react';
import {
  TextField,
  InputAdornment,
  TextFieldProps,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { debounce } from 'lodash';

interface SearchFieldProps extends Omit<TextFieldProps, 'onChange'> {
  onSearch: (value: string) => void;
  debounceTime?: number;
}

const SearchField: FC<SearchFieldProps> = ({
  onSearch,
  debounceTime = 300,
  ...props
}) => {
  const [value, setValue] = useState('');

  const debouncedSearch = debounce((searchValue: string) => {
    onSearch(searchValue);
  }, debounceTime);

  useEffect(() => {
    return () => {
      debouncedSearch.cancel();
    };
  }, [debouncedSearch]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setValue(newValue);
    debouncedSearch(newValue);
  };

  return (
    <TextField
      {...props}
      value={value}
      onChange={handleChange}
      variant="outlined"
      size="small"
      InputProps={{
        ...props.InputProps,
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
      }}
    />
  );
};

export default SearchField;