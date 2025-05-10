import React, { Suspense } from 'react';
import { Grid, Alert, IconButton, Box, CircularProgress } from '@mui/material';
import { PageHeader } from '../components/core';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import {
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
  Assignment as AssignmentIcon,
  Construction as ConstructionIcon,
} from '@mui/icons-material';
import { useDashboardData } from '../hooks/useDashboardData';
import { useTrendCalculator } from '../hooks/useTrendCalculator';
import StatsCard from '../components/dashboard/StatsCard';

// Lazy load components
const ActivityFeed = React.lazy(() => import('../components/dashboard/ActivityFeed'));
const QuickActions = React.lazy(() => import('../components/dashboard/QuickActions'));
const ChartsSection = React.lazy(() => import('../components/dashboard/ChartsSection'));

// Loading fallback component
const ComponentLoader = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
    <CircularProgress />
  </Box>
);

const DashboardPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useDashboardData();
  const calculateTrend = useTrendCalculator();
  const breadcrumbs = [
    { label: 'الرئيسية', link: '/dashboard' },
  ];

  return (
    <>
      {error ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          حدث خطأ أثناء تحميل البيانات. الرجاء المحاولة مرة أخرى.
        </Alert>
      ) : null}

      <PageHeader
        title="لوحة التحكم"
        subtitle="نظرة عامة على النشاط والإحصائيات"
        breadcrumbs={breadcrumbs}
        actions={[
          {
            label: 'تحديث',
            icon: <RefreshIcon />,
            onClick: () => refetch(),
            variant: 'outlined',
            color: 'primary'
          }
        ]}
      />
      
      <Grid container spacing={3}>
        {/* Quick Stats - Keep these eagerly loaded for better UX */}
        <Grid item xs={12} md={6} lg={3}>
          <StatsCard
            title="العملاء النشطين"
            value={data?.stats.activeCustomers.toLocaleString() ?? '0'}
            icon={PeopleIcon}
            color="primary"
            isLoading={isLoading}
            trend={calculateTrend({
              currentValue: data?.stats.activeCustomers ?? 0,
              type: 'monthly'
            })}
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatsCard
            title="الطلبات الجديدة"
            value={data?.stats.newOrders.toLocaleString() ?? '0'}
            icon={ShoppingCartIcon}
            color="info"
            isLoading={isLoading}
            trend={calculateTrend({
              currentValue: data?.stats.newOrders ?? 0,
              type: 'weekly'
            })}
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatsCard
            title="المعاينات اليوم"
            value={data?.stats.todayInspections.toLocaleString() ?? '0'}
            icon={AssignmentIcon}
            color="warning"
            isLoading={isLoading}
            trend={calculateTrend({
              currentValue: data?.stats.todayInspections ?? 0,
              type: 'daily'
            })}
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatsCard
            title="التركيبات المجدولة"
            value={data?.stats.scheduledInstallations.toLocaleString() ?? '0'}
            icon={ConstructionIcon}
            color="success"
            isLoading={isLoading}
            trend={calculateTrend({
              currentValue: data?.stats.scheduledInstallations ?? 0,
              type: 'weekly'
            })}
          />
        </Grid>

        {/* Lazy loaded components */}
        <Grid item xs={12} md={8}>
          <Suspense fallback={<ComponentLoader />}>
            <ActivityFeed 
              activities={data?.activities ?? []} 
              isLoading={isLoading}
            />
          </Suspense>
        </Grid>

        <Grid item xs={12} md={4}>
          <Suspense fallback={<ComponentLoader />}>
            <QuickActions isLoading={isLoading} />
          </Suspense>
        </Grid>

        <Grid item xs={12}>
          <Suspense fallback={<ComponentLoader />}>
            <ChartsSection 
              refreshKey={data ? Date.now() : undefined} 
              isLoading={isLoading}
            />
          </Suspense>
        </Grid>
      </Grid>
    </>
  );
};

export default DashboardPage;
