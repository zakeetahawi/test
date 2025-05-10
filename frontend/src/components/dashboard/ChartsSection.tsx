import React from 'react';
import { Grid, Paper, Typography, Box, Skeleton } from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  TooltipProps,
} from 'recharts';
import { useTheme } from '@mui/material/styles';
import { generateMockSalesData, generateMockOrderDistribution } from '../../utils/mockData';

interface SalesData {
  month: string;
  amount: number;
}

interface OrderData {
  name: string;
  value: number;
}

interface PieLabelProps {
  name: string;
  percent: number;
}

interface ChartsSectionProps {
  refreshKey?: number; // Used to trigger re-render with new data
  isLoading?: boolean;
}

const ChartsSection: React.FC<ChartsSectionProps> = ({ refreshKey, isLoading }) => {
  // Re-generate data when refreshKey changes
  const salesData: SalesData[] = React.useMemo(() => generateMockSalesData(), [refreshKey]);
  const orderDistributionData: OrderData[] = React.useMemo(() => generateMockOrderDistribution(), [refreshKey]);
  const theme = useTheme();

  const COLORS = [
    theme.palette.primary.main,
    theme.palette.info.main,
    theme.palette.success.main,
    theme.palette.warning.main,
  ];

  const formatCurrency = (value: number): string => {
    return `${value.toLocaleString('ar-EG')} ج.م`;
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Paper
          sx={{
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            height: 400,
          }}
        >
          <Typography variant="h6" gutterBottom>
            إحصائيات المبيعات
          </Typography>
          {isLoading ? (
            <Box sx={{ p: 3 }}>
              <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 1 }} />
            </Box>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={salesData}
                margin={{
                  top: 20,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={formatCurrency} />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  labelStyle={{ fontFamily: 'Cairo' }}
                />
                <Bar dataKey="amount" fill={theme.palette.primary.main} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Paper>
      </Grid>
      <Grid item xs={12} md={6}>
        <Paper
          sx={{
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            height: 400,
          }}
        >
          <Typography variant="h6" gutterBottom>
            توزيع الطلبات
          </Typography>
          {isLoading ? (
            <Box sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Skeleton variant="circular" width={240} height={240} />
            </Box>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={orderDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: PieLabelProps) => 
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {orderDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
};

export default ChartsSection;
