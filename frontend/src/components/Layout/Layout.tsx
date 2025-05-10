import React, { useState } from 'react';
import { useNavigate, useLocation, Routes, Route } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  Button,
  Badge,
  Menu,
  MenuItem,
  ListItem,
  ListItemIcon,
  ListItemText,
  Select,
  SelectChangeEvent,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Person as PersonIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
  Inventory as InventoryIcon,
  Build as BuildIcon,
  Assignment as AssignmentIcon,
  Construction as ConstructionIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  CloudUpload as CloudUploadIcon,
  ImportExport as ImportExportIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { arEG } from 'date-fns/locale';
import { useAuth } from '../../hooks/useAuth';
import { Logo } from './Logo';
import { useAppTheme } from '../../theme/ThemeProvider';
import { useNotifications, StatusLabel } from '../core';

// Import all pages
import DashboardPage from '../../pages/DashboardPage';
import CustomersPage from '../../pages/CustomersPage';
import OrdersPage from '../../pages/OrdersPage';
import InventoryPage from '../../pages/InventoryPage';
import FactoryPage from '../../pages/FactoryPage';
import InspectionsPage from '../../pages/InspectionsPage';
import InstallationsPage from '../../pages/InstallationsPage';
import ReportsPage from '../../pages/ReportsPage';
import SettingsPage from '../../pages/SettingsPage';

const drawerWidth = 240;

interface Notification {
  id: number;
  title: string;
  priority: 'urgent' | 'high' | 'normal';
  created_at: string;
  is_read: boolean;
}

export const Layout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorElNotifications, setAnchorElNotifications] = useState<null | HTMLElement>(null);
  const [anchorElUser, setAnchorElUser] = useState<null | HTMLElement>(null);
  const [selectedTheme, setSelectedTheme] = useState('default');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { theme, currentTheme, changeTheme } = useAppTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const notify = useNotifications();

  const menuItems = [
    { text: 'الرئيسية', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'العملاء', icon: <PeopleIcon />, path: '/customers' },
    { text: 'الطلبات', icon: <ShoppingCartIcon />, path: '/orders' },
    { text: 'المخزون', icon: <InventoryIcon />, path: '/inventory' },
    { text: 'المصنع', icon: <BuildIcon />, path: '/factory' },
    { text: 'المعاينات', icon: <AssignmentIcon />, path: '/inspections' },
    { text: 'التركيبات', icon: <ConstructionIcon />, path: '/installations' },
    { text: 'التقارير', icon: <AssessmentIcon />, path: '/reports' },
    { text: 'الإعدادات', icon: <SettingsIcon />, path: '/settings' },
  ];

  const dataManagementItems = [
    { text: 'استيراد وتصدير البيانات', icon: <ImportExportIcon />, path: '/data-import-export' },
    { text: 'النسخ الاحتياطي والتخزين السحابي', icon: <CloudUploadIcon />, path: '/data-backup' },
  ];

  const unreadNotificationsCount = notifications.filter(n => !n.is_read).length;

  const handleThemeChange = (event: SelectChangeEvent) => {
    const newTheme = event.target.value;
    setSelectedTheme(newTheme);
    changeTheme(newTheme);
    notify.showSuccess('تم تغيير المظهر بنجاح');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    notify.showInfo('تم تسجيل الخروج بنجاح');
  };

  const drawer = (
    <div>
      <Toolbar>
        <Logo />
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            selected={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
        <Divider />
        {user?.is_superuser && (
          <>
            <ListItem>
              <Typography variant="subtitle2" color="textSecondary" sx={{ px: 2, py: 1 }}>
                إدارة البيانات
              </Typography>
            </ListItem>
            {dataManagementItems.map((item) => (
              <ListItem
                button
                key={item.text}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
          </>
        )}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex', direction: 'rtl' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mr: { sm: `${drawerWidth}px` },
          backgroundColor: theme.palette.primary.main,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find(item => item.path === location.pathname)?.text || 'نظام إدارة العملاء'}
          </Typography>

          <IconButton
            color="inherit"
            onClick={(event) => setAnchorElNotifications(event.currentTarget)}
          >
            <Badge badgeContent={unreadNotificationsCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          <Button
            color="inherit"
            onClick={(event) => setAnchorElUser(event.currentTarget)}
            startIcon={<PersonIcon />}
            sx={{ mr: 2 }}
          >
            {user?.full_name || user?.username}
          </Button>

          <Menu
            anchorEl={anchorElNotifications}
            open={Boolean(anchorElNotifications)}
            onClose={() => setAnchorElNotifications(null)}
            PaperProps={{
              sx: { width: 350, maxHeight: 400 }
            }}
          >
            <MenuItem>
              <Typography variant="h6">الإشعارات</Typography>
            </MenuItem>
            <Divider />
            {notifications.length > 0 ? (
              notifications.map((notification) => (
                <MenuItem
                  key={notification.id}
                  onClick={() => {
                    navigate(`/notifications/${notification.id}`);
                    setAnchorElNotifications(null);
                  }}
                  sx={{
                    backgroundColor: notification.is_read ? 'inherit' : 'action.hover',
                  }}
                >
                  <Box sx={{ width: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="subtitle2" component="span">
                        {notification.title}
                      </Typography>
                      <Box sx={{ ml: 1 }}>
                        {notification.priority === 'urgent' && (
                          <StatusLabel status="blocked" />
                        )}
                      </Box>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {format(new Date(notification.created_at), 'PP', { locale: arEG })}
                    </Typography>
                  </Box>
                </MenuItem>
              ))
            ) : (
              <MenuItem>
                <Typography color="text.secondary">لا توجد إشعارات</Typography>
              </MenuItem>
            )}
            <Divider />
            <MenuItem
              onClick={() => {
                navigate('/notifications');
                setAnchorElNotifications(null);
              }}
            >
              <Typography align="center" sx={{ width: '100%' }}>
                عرض كل الإشعارات
              </Typography>
            </MenuItem>
          </Menu>

          <Menu
            anchorEl={anchorElUser}
            open={Boolean(anchorElUser)}
            onClose={() => setAnchorElUser(null)}
          >
            <MenuItem sx={{ px: 3, py: 2 }}>
              <Select
                value={selectedTheme}
                onChange={handleThemeChange}
                fullWidth
                size="small"
              >
                <MenuItem value="default">الثيم الافتراضي</MenuItem>
                <MenuItem value="light-sky">السماوي الفاتح</MenuItem>
                <MenuItem value="soft-pink">الوردي الناعم</MenuItem>
                <MenuItem value="fresh-mint">الأخضر المنعش</MenuItem>
                <MenuItem value="calm-lavender">البنفسجي الهادئ</MenuItem>
                <MenuItem value="warm-beige">البيج الدافئ</MenuItem>
              </Select>
            </MenuItem>
            <Divider />
            <MenuItem
              onClick={() => {
                navigate('/profile');
                setAnchorElUser(null);
              }}
            >
              <ListItemIcon><PersonIcon fontSize="small" /></ListItemIcon>
              الملف الشخصي 
            </MenuItem>
            {user?.is_staff && (
              <MenuItem
                onClick={() => {
                  navigate('/admin');
                  setAnchorElUser(null);
                }}
              >
                <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
                لوحة الإدارة
              </MenuItem>
            )}
            <Divider />
            <MenuItem onClick={handleLogout}>تسجيل الخروج</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          anchor="right"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          anchor="right"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          marginTop: '64px',
        }}
      >
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/customers/*" element={<CustomersPage />} />
          <Route path="/orders/*" element={<OrdersPage />} />
          <Route path="/inventory/*" element={<InventoryPage />} />
          <Route path="/factory/*" element={<FactoryPage />} />
          <Route path="/inspections/*" element={<InspectionsPage />} />
          <Route path="/installations/*" element={<InstallationsPage />} />
          <Route path="/reports/*" element={<ReportsPage />} />
          <Route path="/settings/*" element={<SettingsPage />} />
        </Routes>
      </Box>
    </Box>
  );
};
