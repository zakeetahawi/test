import React, { useState } from 'react';
import {
    Drawer,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Collapse,
    IconButton,
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    People as PeopleIcon,
    Inventory as InventoryIcon,
    Assignment as OrdersIcon,
    Build as FactoryIcon,
    Assessment as ReportsIcon,
    ExpandLess,
    ExpandMore,
    ChevronRight,
    ChevronLeft,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '../../hooks/redux';

const drawerWidth = 240;

export const Navigation: React.FC = () => {
    const [open, setOpen] = useState(true);
    const [selectedMenu, setSelectedMenu] = useState<string | null>(null);
    const { user } = useAppSelector((state) => state.auth);
    const navigate = useNavigate();
    const location = useLocation();

    const menuItems = [
        {
            title: 'لوحة التحكم',
            icon: <DashboardIcon />,
            path: '/',
        },
        {
            title: 'العملاء',
            icon: <PeopleIcon />,
            path: '/customers',
            subItems: [
                { title: 'قائمة العملاء', path: '/customers' },
                { title: 'إضافة عميل', path: '/customers/add' },
            ],
        },
        {
            title: 'المخزون',
            icon: <InventoryIcon />,
            path: '/inventory',
            subItems: [
                { title: 'المنتجات', path: '/inventory/products' },
                { title: 'الوحدات', path: '/inventory/units' },
            ],
        },
        {
            title: 'الطلبات',
            icon: <OrdersIcon />,
            path: '/orders',
            subItems: [
                { title: 'قائمة الطلبات', path: '/orders' },
                { title: 'طلب جديد', path: '/orders/new' },
            ],
        },
        {
            title: 'المصنع',
            icon: <FactoryIcon />,
            path: '/factory',
            subItems: [
                { title: 'خط الإنتاج', path: '/factory/production' },
                { title: 'التفتيش', path: '/factory/inspection' },
            ],
        },
        {
            title: 'التقارير',
            icon: <ReportsIcon />,
            path: '/reports',
        },
    ];

    const handleMenuClick = (path: string, hasSubItems?: boolean) => {
        if (hasSubItems) {
            setSelectedMenu(selectedMenu === path ? null : path);
        } else {
            navigate(path);
        }
    };

    return (
        <Drawer
            variant="permanent"
            sx={{
                width: open ? drawerWidth : 56,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                    width: open ? drawerWidth : 56,
                    boxSizing: 'border-box',
                    overflowX: 'hidden',
                    transition: 'width 0.2s',
                },
            }}
        >
            <IconButton
                onClick={() => setOpen(!open)}
                sx={{
                    position: 'absolute',
                    right: 0,
                    top: '64px',
                    zIndex: 1,
                }}
            >
                {open ? <ChevronRight /> : <ChevronLeft />}
            </IconButton>
            <List sx={{ mt: 8 }}>
                {menuItems.map((item) => (
                    <React.Fragment key={item.path}>
                        <ListItem
                            button
                            onClick={() => handleMenuClick(item.path, !!item.subItems)}
                            selected={location.pathname === item.path}
                        >
                            <ListItemIcon>{item.icon}</ListItemIcon>
                            {open && (
                                <>
                                    <ListItemText primary={item.title} />
                                    {item.subItems && (
                                        <>
                                            {selectedMenu === item.path ? (
                                                <ExpandLess />
                                            ) : (
                                                <ExpandMore />
                                            )}
                                        </>
                                    )}
                                </>
                            )}
                        </ListItem>
                        {item.subItems && (
                            <Collapse
                                in={selectedMenu === item.path && open}
                                timeout="auto"
                                unmountOnExit
                            >
                                <List component="div" disablePadding>
                                    {item.subItems.map((subItem) => (
                                        <ListItem
                                            key={subItem.path}
                                            button
                                            onClick={() => navigate(subItem.path)}
                                            selected={location.pathname === subItem.path}
                                            sx={{ pl: 4 }}
                                        >
                                            <ListItemText primary={subItem.title} />
                                        </ListItem>
                                    ))}
                                </List>
                            </Collapse>
                        )}
                    </React.Fragment>
                ))}
            </List>
        </Drawer>
    );
};