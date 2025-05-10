import { FC, ReactNode } from 'react';
import {
  TextField,
  TextFieldProps,
  FormControl,
  FormHelperText,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  FormLabel,
  RadioGroup,
  Radio,
  Switch,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useTranslation } from 'react-i18next';

type FieldType =
  | 'text'
  | 'number'
  | 'email'
  | 'password'
  | 'tel'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'checkbox'
  | 'radio'
  | 'switch'
  | 'date';

interface Option {
  value: string | number;
  label: string;
}

interface FormFieldProps extends Omit<TextFieldProps, 'type'> {
  type: FieldType;
  options?: Option[];
  error?: boolean;
  helperText?: string;
  value: any;
  onChange: (value: any) => void;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  startAdornment?: ReactNode;
  endAdornment?: ReactNode;
}

const FormField: FC<FormFieldProps> = ({
  type,
  options = [],
  error,
  helperText,
  value,
  onChange,
  label,
  required,
  disabled,
  fullWidth = true,
  startAdornment,
  endAdornment,
  ...props
}) => {
  const { t } = useTranslation();

  switch (type) {
    case 'select':
    case 'multiselect':
      return (
        <FormControl
          fullWidth={fullWidth}
          error={error}
          required={required}
          disabled={disabled}
        >
          <InputLabel>{label}</InputLabel>
          <Select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            multiple={type === 'multiselect'}
            label={label}
          >
            {options.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
          {helperText && <FormHelperText>{helperText}</FormHelperText>}
        </FormControl>
      );

    case 'checkbox':
      return (
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(value)}
              onChange={(e) => onChange(e.target.checked)}
              disabled={disabled}
            />
          }
          label={label || ''}
        />
      );

    case 'radio':
      return (
        <FormControl
          component="fieldset"
          error={error}
          required={required}
          disabled={disabled}
        >
          <FormLabel component="legend">{label}</FormLabel>
          <RadioGroup
            value={value}
            onChange={(e) => onChange(e.target.value)}
          >
            {options.map((option) => (
              <FormControlLabel
                key={option.value}
                value={option.value}
                control={<Radio />}
                label={option.label}
              />
            ))}
          </RadioGroup>
          {helperText && <FormHelperText>{helperText}</FormHelperText>}
        </FormControl>
      );

    case 'switch':
      return (
        <FormControlLabel
          control={
            <Switch
              checked={Boolean(value)}
              onChange={(e) => onChange(e.target.checked)}
              disabled={disabled}
            />
          }
          label={label || ''}
        />
      );

    case 'date':
      return (
        <DatePicker
          value={value}
          onChange={onChange}
          label={label}
          disabled={disabled}
          slotProps={{
            textField: {
              fullWidth,
              error,
              helperText,
              required,
            },
          }}
        />
      );

    case 'textarea':
      return (
        <TextField
          {...props}
          multiline
          rows={4}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          label={label}
          error={error}
          helperText={helperText}
          required={required}
          disabled={disabled}
          fullWidth={fullWidth}
          InputProps={{
            startAdornment,
            endAdornment,
          }}
        />
      );

    default:
      return (
        <TextField
          {...props}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          label={label}
          error={error}
          helperText={helperText}
          required={required}
          disabled={disabled}
          fullWidth={fullWidth}
          InputProps={{
            startAdornment,
            endAdornment,
          }}
        />
      );
  }
};

export default FormField;