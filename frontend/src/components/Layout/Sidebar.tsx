import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import InventoryIcon from '@mui/icons-material/Inventory';
import BuildIcon from '@mui/icons-material/Build';
import FactoryIcon from '@mui/icons-material/Factory';
import AssignmentIcon from '@mui/icons-material/Assignment';
import SettingsIcon from '@mui/icons-material/Settings';

export const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { text: 'لوحة التحكم', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'العملاء', icon: <PeopleIcon />, path: '/customers' },
    { text: 'الطلبات', icon: <ShoppingCartIcon />, path: '/orders' },
    { text: 'المخزون', icon: <InventoryIcon />, path: '/inventory' },
    { text: 'التركيبات', icon: <BuildIcon />, path: '/installations' },
    { text: 'المصنع', icon: <FactoryIcon />, path: '/factory' },
    { text: 'التقارير', icon: <AssignmentIcon />, path: '/reports' },
    { text: 'الإعدادات', icon: <SettingsIcon />, path: '/settings' },
  ];

  return (
    <Box sx={{ mt: 8 }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" color="primary">
          نظام الخواجه
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => navigate(item.path)}
            selected={location.pathname === item.path}
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'primary.light',
                '&:hover': {
                  backgroundColor: 'primary.light',
                },
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
      <Divider />
    </Box>
  );
};