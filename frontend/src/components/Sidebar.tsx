import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  useTheme,
  styled,
  Typography,
  Divider,
  useMediaQuery,
  Collapse,
  Box
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  People as CustomersIcon,
  Inventory as InventoryIcon,
  Assignment as OrdersIcon,
  Build as InstallationIcon,
  Search as SearchIcon,
  ExpandLess,
  ExpandMore,
  ChevronRight,
  Settings,
} from '@mui/icons-material';

const drawerWidth = 240;

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: 'flex-start',
}));

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const menuItems = [
  {
    title: 'لوحة التحكم',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    title: 'العملاء',
    icon: <CustomersIcon />,
    path: '/customers',
    submenu: [
      { title: 'قائمة العملاء', path: '/customers/list' },
      { title: 'إضافة عميل', path: '/customers/add' },
    ]
  },
  {
    title: 'المخزون',
    icon: <InventoryIcon />,
    path: '/inventory',
    submenu: [
      { title: 'المنتجات', path: '/inventory/products' },
      { title: 'المعاملات', path: '/inventory/transactions' },
    ]
  },
  {
    title: 'الطلبات',
    icon: <OrdersIcon />,
    path: '/orders',
  },
  {
    title: 'التركيبات',
    icon: <InstallationIcon />,
    path: '/installations',
  }
];

export const Sidebar = ({ open, onClose }: SidebarProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [expandedMenu, setExpandedMenu] = useState<string | null>(null);

  const handleMenuClick = (item: typeof menuItems[0]) => {
    if (item.submenu) {
      setExpandedMenu(expandedMenu === item.title ? null : item.title);
    } else {
      navigate(item.path);
      if (isMobile) {
        onClose();
      }
    }
  };

  const handleSubmenuClick = (path: string) => {
    navigate(path);
    if (isMobile) {
      onClose();
    }
  };

  const drawerContent = (
    <>
      <DrawerHeader>
        <IconButton onClick={onClose}>
          <ChevronRight />
        </IconButton>
        <Typography variant="h6" sx={{ flexGrow: 1, textAlign: 'center' }}>
          القائمة
        </Typography>
      </DrawerHeader>
      <Divider />
      <Box sx={{ width: '100%', p: 2 }}>
        <div style={{ position: 'relative', marginBottom: 2 }}>
          <SearchIcon sx={{ position: 'absolute', left: 8, top: 8, color: 'text.secondary' }} />
          <input
            type="text"
            placeholder="بحث..."
            style={{
              width: '100%',
              padding: '8px 35px 8px 8px',
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: '4px',
              outline: 'none',
            }}
          />
        </div>
      </Box>
      <List>
        {menuItems.map((item) => (
          <>
            <ListItem
              button
              onClick={() => handleMenuClick(item)}
              sx={{
                py: 1,
                '&:hover': {
                  backgroundColor: theme.palette.action.hover,
                }
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.title} />
              {item.submenu && (expandedMenu === item.title ? <ExpandLess /> : <ExpandMore />)}
            </ListItem>
            {item.submenu && (
              <Collapse in={expandedMenu === item.title} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {item.submenu.map((subItem) => (
                    <ListItem
                      button
                      onClick={() => handleSubmenuClick(subItem.path)}
                      sx={{
                        py: 1,
                        pl: 4,
                        '&:hover': {
                          backgroundColor: theme.palette.action.hover,
                        }
                      }}
                    >
                      <ListItemText primary={subItem.title} />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            )}
          </>
        ))}
      </List>
      <Divider />
      <List>
        <ListItem 
          button 
          sx={{ py: 1 }}
          onClick={() => handleSubmenuClick('/settings')}
        >
          <ListItemIcon>
            <Settings />
          </ListItemIcon>
          <ListItemText primary="الإعدادات" />
        </ListItem>
      </List>
    </>
  );

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'persistent'}
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};