import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Button,
  Grid
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { formatDate, formatCurrency } from '../../utils/formatters';

interface AffectedOrder {
  order_number: string;
  current_price: number;
  new_price: number;
  price_difference: number;
  customer: string;
  created_at: string;
}

interface DynamicPricingRule {
  id: number;
  name: string;
  rule_type: string;
  discount_percentage: number;
  min_quantity?: number;
  min_amount?: number;
  customer_type?: string;
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
  priority: number;
  description?: string;
}

interface Props {
  ruleId: number;
}

export const DynamicPricingDetails: React.FC<Props> = ({ ruleId }) => {
  const queryClient = useQueryClient();

  const { data: rule, isLoading: isLoadingRule } = useQuery<DynamicPricingRule>({
    queryKey: ['dynamicPricingRule', ruleId],
    queryFn: () => api.get(`/orders/api/dynamic-pricing/${ruleId}/`).then(res => res.data)
  });

  const { data: affectedOrders = [], isLoading: isLoadingOrders } = useQuery<AffectedOrder[]>({
    queryKey: ['affectedOrders', ruleId],
    queryFn: () => api.get(`/orders/api/dynamic-pricing/${ruleId}/affected_orders/`).then(res => res.data)
  });

  const applyToOrdersMutation = useMutation({
    mutationFn: (orderIds: number[]) => 
      api.post('/orders/api/dynamic-pricing/apply_to_orders/', { order_ids: orderIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['affectedOrders'] });
    }
  });

  const handleApplyToAll = () => {
    const orderIds = affectedOrders.map(order => parseInt(order.order_number.split('-')[1]));
    applyToOrdersMutation.mutate(orderIds);
  };

  if (isLoadingRule || !rule) {
    return <Alert severity="info">جاري تحميل بيانات القاعدة...</Alert>;
  }

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            {rule.name}
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                نوع القاعدة
              </Typography>
              <Chip
                label={
                  rule.rule_type === 'seasonal' ? 'موسمي' :
                  rule.rule_type === 'quantity' ? 'كمية' :
                  rule.rule_type === 'customer_type' ? 'نوع العميل' : 'عرض خاص'
                }
                color="primary"
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                نسبة الخصم
              </Typography>
              <Typography>
                {rule.discount_percentage}%
              </Typography>
            </Grid>
            
            {rule.min_quantity && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  الحد الأدنى للكمية
                </Typography>
                <Typography>
                  {rule.min_quantity}
                </Typography>
              </Grid>
            )}
            
            {rule.min_amount && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  الحد الأدنى للمبلغ
                </Typography>
                <Typography>
                  {formatCurrency(rule.min_amount)}
                </Typography>
              </Grid>
            )}
            
            {rule.customer_type && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  نوع العميل
                </Typography>
                <Typography>
                  {rule.customer_type === 'regular' ? 'عادي' :
                   rule.customer_type === 'vip' ? 'VIP' :
                   rule.customer_type === 'wholesale' ? 'جملة' : 'موزع'}
                </Typography>
              </Grid>
            )}
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                الفترة
              </Typography>
              <Typography>
                {rule.start_date ? formatDate(rule.start_date) : 'غير محدد'} - {rule.end_date ? formatDate(rule.end_date) : 'غير محدد'}
              </Typography>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary">
                الوصف
              </Typography>
              <Typography>
                {rule.description || 'لا يوجد وصف'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              الطلبات المتأثرة
            </Typography>
            {affectedOrders.length > 0 && (
              <Button
                variant="contained"
                color="primary"
                onClick={handleApplyToAll}
                disabled={applyToOrdersMutation.isLoading}
              >
                تطبيق على جميع الطلبات
              </Button>
            )}
          </Box>

          {isLoadingOrders ? (
            <Alert severity="info">جاري تحميل الطلبات المتأثرة...</Alert>
          ) : affectedOrders.length === 0 ? (
            <Alert severity="info">لا توجد طلبات متأثرة بهذه القاعدة حالياً</Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>رقم الطلب</TableCell>
                    <TableCell>العميل</TableCell>
                    <TableCell align="right">السعر الحالي</TableCell>
                    <TableCell align="right">السعر الجديد</TableCell>
                    <TableCell align="right">الفرق</TableCell>
                    <TableCell>تاريخ الإنشاء</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {affectedOrders.map((order) => (
                    <TableRow key={order.order_number}>
                      <TableCell>{order.order_number}</TableCell>
                      <TableCell>{order.customer}</TableCell>
                      <TableCell align="right">{formatCurrency(order.current_price)}</TableCell>
                      <TableCell align="right">{formatCurrency(order.new_price)}</TableCell>
                      <TableCell 
                        align="right"
                        sx={{
                          color: order.price_difference < 0 ? 'success.main' : 'error.main'
                        }}
                      >
                        {order.price_difference < 0 ? '-' : '+'}
                        {formatCurrency(Math.abs(order.price_difference))}
                      </TableCell>
                      <TableCell>{formatDate(order.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};