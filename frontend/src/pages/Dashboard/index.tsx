import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  useTheme
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Person as PersonIcon,
  ShoppingCart as ShoppingCartIcon,
  Inventory as InventoryIcon,
  AttachMoney as MoneyIcon
} from '@mui/icons-material';
import dashboardService, { 
  DashboardStats, 
  RecentActivity, 
  RecentOrder,
  TrendsData 
} from '../../services/dashboardService';
import { dashboardStyles } from './styles';
import DashboardChart from './DashboardChart';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const styles = dashboardStyles(theme);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([]);
  const [trendsData, setTrendsData] = useState<TrendsData | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsData, activitiesData, ordersData, trendsData] = await Promise.all([
          dashboardService.getStats(),
          dashboardService.getRecentActivities(),
          dashboardService.getRecentOrders(),
          dashboardService.getTrends()
        ]);

        setStats(statsData);
        setActivities(activitiesData);
        setRecentOrders(ordersData);
        setTrendsData(trendsData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const StatCard: React.FC<{
    title: string;
    value: number;
    growth: string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, growth, icon, color }) => {
    const isPositive = !growth.startsWith('-');
    const GrowthIcon = isPositive ? TrendingUpIcon : TrendingDownIcon;

    return (
      <Card sx={styles.statCard}>
        <CardContent sx={styles.cardContent}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box sx={{ ...styles.iconContainer, backgroundColor: `${color}15` }}>
              <Box sx={{ color }}>{icon}</Box>
            </Box>
            <Typography variant="h6" component="div">
              {title}
            </Typography>
          </Box>
          <Typography variant="h4" component="div" sx={{ my: 2 }}>
            {value.toLocaleString('ar-EG')}
          </Typography>
          <Box sx={styles.growthIndicator}>
            <GrowthIcon sx={{ 
              color: isPositive ? theme.palette.success.main : theme.palette.error.main 
            }} />
            <Typography 
              variant="body2" 
              color={isPositive ? 'success.main' : 'error.main'}
            >
              {growth}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        لوحة التحكم الرئيسية
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="العملاء"
            value={stats?.totalCustomers || 0}
            growth={stats?.customerGrowth || '0%'}
            icon={<PersonIcon fontSize="large" />}
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="الطلبات"
            value={stats?.totalOrders || 0}
            growth={stats?.orderGrowth || '0%'}
            icon={<ShoppingCartIcon fontSize="large" />}
            color={theme.palette.secondary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="المخزون"
            value={stats?.inventoryValue || 0}
            growth={stats?.inventoryGrowth || '0%'}
            icon={<InventoryIcon fontSize="large" />}
            color={theme.palette.info.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="الإيرادات الشهرية"
            value={stats?.monthlyRevenue || 0}
            growth={stats?.revenueGrowth || '0%'}
            icon={<MoneyIcon fontSize="large" />}
            color={theme.palette.success.main}
          />
        </Grid>
      </Grid>

      {/* Performance Chart */}
      {trendsData && <DashboardChart data={trendsData} />}

      {/* Recent Activities and Orders */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={styles.activityPaper}>
            <Box p={2}>
              <Typography variant="h6" gutterBottom>
                آخر النشاطات
              </Typography>
            </Box>
            <List sx={styles.activityList}>
              {activities.map((activity) => (
                <ListItem key={activity.id} divider>
                  <ListItemText
                    primary={activity.message}
                    secondary={new Date(activity.timestamp).toLocaleString('ar-EG')}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={styles.activityPaper}>
            <Box p={2}>
              <Typography variant="h6" gutterBottom>
                آخر الطلبات
              </Typography>
            </Box>
            <List sx={styles.activityList}>
              {recentOrders.map((order) => (
                <ListItem key={order.id} divider>
                  <ListItemText
                    primary={
                      <Box display="flex" justifyContent="space-between">
                        <Typography>{order.customerName}</Typography>
                        <Typography sx={styles.orderAmount}>
                          {order.amount.toLocaleString('ar-EG')} ج.م
                        </Typography>
                      </Box>
                    }
                    secondary={new Date(order.date).toLocaleString('ar-EG')}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;