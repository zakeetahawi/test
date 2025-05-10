import React from 'react';
import { Grid, Paper, Typography, Box } from '@mui/material';
import {
    People as PeopleIcon,
    Assignment as OrdersIcon,
    Inventory as InventoryIcon,
    TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/redux';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => (
    <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Box sx={{ p: 1, borderRadius: 1, bgcolor: `${color}20`, mr: 2 }}>
                {React.cloneElement(icon as React.ReactElement, { sx: { color } })}
            </Box>
            <Typography variant="h6" component="div">
                {title}
            </Typography>
        </Box>
        <Typography variant="h4" component="div" sx={{ textAlign: 'center' }}>
            {value}
        </Typography>
    </Paper>
);

export const Dashboard: React.FC = () => {
    const { user } = useAppSelector((state) => state.auth);

    const stats = [
        {
            title: 'العملاء النشطون',
            value: '120',
            icon: <PeopleIcon />,
            color: '#1976d2',
        },
        {
            title: 'الطلبات الجديدة',
            value: '25',
            icon: <OrdersIcon />,
            color: '#2e7d32',
        },
        {
            title: 'المنتجات في المخزون',
            value: '450',
            icon: <InventoryIcon />,
            color: '#ed6c02',
        },
        {
            title: 'إجمالي المبيعات',
            value: '₪15,750',
            icon: <TrendingUpIcon />,
            color: '#9c27b0',
        },
    ];

    return (
        <Box>
            <Typography variant="h4" sx={{ mb: 4 }}>
                مرحباً، {user?.first_name || 'مستخدم'}
            </Typography>
            <Grid container spacing={3}>
                {stats.map((stat) => (
                    <Grid item xs={12} sm={6} md={3} key={stat.title}>
                        <StatCard {...stat} />
                    </Grid>
                ))}
            </Grid>
            {/* سيتم إضافة المزيد من المكونات مثل الرسوم البيانية والتقارير لاحقاً */}
        </Box>
    );
};