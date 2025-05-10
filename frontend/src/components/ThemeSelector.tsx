import React from 'react';
import { Select, MenuItem } from '@mui/material';
import { ThemeContext } from '../theme/ThemeProvider';

export const ThemeSelector = () => {
  const { currentTheme, setTheme } = React.useContext(ThemeContext);

  return (
    <Select
      value={currentTheme}
      onChange={(e) => setTheme(e.target.value)}
      size="small"
      sx={{
        '& .MuiSelect-select': {
          py: 1,
          color: 'inherit',
        },
        minWidth: 120,
      }}
    >
      <MenuItem value="default">الثيم الافتراضي</MenuItem>
      <MenuItem value="light-sky">السماوي الفاتح</MenuItem>
      <MenuItem value="soft-pink">الوردي الناعم</MenuItem>
      <MenuItem value="fresh-mint">الأخضر المنعش</MenuItem>
      <MenuItem value="calm-lavender">البنفسجي الهادئ</MenuItem>
      <MenuItem value="warm-beige">البيج الدافئ</MenuItem>
      <MenuItem value="pastel-blue">الأزرق الباستيل</MenuItem>
      <MenuItem value="peachy-yellow">الأصفر المشمشي</MenuItem>
      <MenuItem value="light-gray">الرمادي الفاتح</MenuItem>
      <MenuItem value="light-turquoise">التركواز الفاتح</MenuItem>
    </Select>
  );
};