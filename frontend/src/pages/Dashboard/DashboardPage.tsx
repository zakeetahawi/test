import { useEffect, useState } from 'react';
import { Grid, Container } from '@mui/material';
import {
  People as PeopleIcon,
  ShoppingCart as OrdersIcon,
  AttachMoney as RevenueIcon,
  Build as InstallationIcon,
  Inventory as InventoryIcon,
  Assignment as InspectionIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { StatCard } from '../../components/dashboard/StatCard';
import { DashboardChart } from '../../components/dashboard/DashboardChart';
import { dashboardService, DashboardStats } from '../../services/dashboardService';
import { formatCurrency } from '../../utils/formatters';

export const DashboardPage = () => {
  const { data: stats, isLoading } = useQuery<DashboardStats>(
    'dashboardStats',
    dashboardService.getDashboardStats
  );

  const revenueChartData = {
    labels: stats?.revenueData.labels || [],
    datasets: [
      {
        label: 'الإيرادات',
        data: stats?.revenueData.data || [],
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        fill: true,
      },
    ],
  };

  const ordersChartData = {
    labels: stats?.ordersData.labels || [],
    datasets: [
      {
        label: 'الطلبات',
        data: stats?.ordersData.data || [],
        backgroundColor: '#4caf50',
      },
    ],
  };

  if (isLoading) {
    return <div>جاري التحميل...</div>;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        {/* إحصائيات سريعة */}
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="العملاء"
            value={stats?.totalCustomers || 0}
            icon={<PeopleIcon />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="الطلبات"
            value={stats?.totalOrders || 0}
            icon={<OrdersIcon />}
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="الإيرادات"
            value={formatCurrency(stats?.totalRevenue || 0)}
            icon={<RevenueIcon />}
            color="info.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="تركيبات معلقة"
            value={stats?.pendingInstallations || 0}
            icon={<InstallationIcon />}
            color="warning.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="قيمة المخزون"
            value={formatCurrency(stats?.inventoryValue || 0)}
            icon={<InventoryIcon />}
            color="error.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="تفتيش معلق"
            value={stats?.pendingInspections || 0}
            icon={<InspectionIcon />}
            color="secondary.main"
          />
        </Grid>

        {/* الرسوم البيانية */}
        <Grid item xs={12} md={8}>
          <DashboardChart
            title="الإيرادات الشهرية"
            type="line"
            data={revenueChartData}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <DashboardChart
            title="الطلبات الشهرية"
            type="bar"
            data={ordersChartData}
          />
        </Grid>
      </Grid>
    </Container>
  );
};