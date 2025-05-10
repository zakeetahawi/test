import { FC } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Inventory as InventoryIcon,
  ShoppingCart as OrdersIcon,
  Build as FactoryIcon,
  Assignment as InspectionsIcon,
  Engineering as InstallationsIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

const menuItems = [
  { text: 'لوحة التحكم', icon: <DashboardIcon />, path: '/' },
  { text: 'العملاء', icon: <PeopleIcon />, path: '/customers' },
  { text: 'المخزون', icon: <InventoryIcon />, path: '/inventory' },
  { text: 'الطلبات', icon: <OrdersIcon />, path: '/orders' },
  { text: 'المصنع', icon: <FactoryIcon />, path: '/factory' },
  { text: 'التفتيش', icon: <InspectionsIcon />, path: '/inspections' },
  { text: 'التركيبات', icon: <InstallationsIcon />, path: '/installations' },
  { text: 'التقارير', icon: <ReportsIcon />, path: '/reports' },
  { text: 'الإعدادات', icon: <SettingsIcon />, path: '/settings' },
];

const Sidebar: FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ overflow: 'auto' }}>
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="h6" component="div">
          CRM System
        </Typography>
      </Box>
      <Divider />
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
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default Sidebar;