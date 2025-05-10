import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  InputAdornment,
  Link
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

interface TestRuleResponse {
  is_applicable: boolean;
  current_price?: number;
  test_price?: number;
  discount_amount?: number;
  reason?: string;
}

interface Order {
  id: number;
  order_number: string;
  total_amount: number;
  customer: {
    name: string;
    customer_type: string;
  };
}

export const PricingRuleTest: React.FC = () => {
  const [orderId, setOrderId] = useState('');
  const [ruleData, setRuleData] = useState({
    name: 'قاعدة اختبار',
    rule_type: 'quantity',
    discount_percentage: 0,
    min_quantity: 0,
    min_amount: 0,
    customer_type: '',
    start_date: null as Date | null,
    end_date: null as Date | null,
    is_active: true
  });

  const testMutation = useMutation({
    mutationFn: () =>
      api.post<TestRuleResponse>('/orders/api/dynamic-pricing/test-rule/', {
        order_id: orderId,
        rule: ruleData
      }),
    onError: (error: any) => {
      console.error('خطأ في اختبار القاعدة:', error);
    }
  });

  const { data: recentOrders } = useQuery({
    queryKey: ['recentOrders'],
    queryFn: () =>
      api.get<Order[]>('/orders/api/orders/', {
        params: {
          status: ['pending', 'processing'],
          limit: 5,
          ordering: '-created_at'
        }
      }).then(res => res.data)
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    testMutation.mutate();
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          اختبار قاعدة التسعير
        </Typography>

        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="رقم الطلب"
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                required
              />
            </Grid>

            {recentOrders && recentOrders.length > 0 && (
              <Box mt={1} mb={2}>
                <Typography variant="caption" display="block" gutterBottom>
                  الطلبات الأخيرة للاختبار:
                </Typography>
                {recentOrders.map(order => (
                  <Link
                    key={order.id}
                    component="button"
                    variant="body2"
                    onClick={() => setOrderId(order.id.toString())}
                    sx={{ mr: 2 }}
                  >
                    {order.order_number} ({order.customer.name})
                  </Link>
                ))}
              </Box>
            )}

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="نوع القاعدة"
                value={ruleData.rule_type}
                onChange={(e) =>
                  setRuleData({ ...ruleData, rule_type: e.target.value })
                }
                SelectProps={{ native: true }}
              >
                <option value="quantity">كمية</option>
                <option value="customer_type">نوع العميل</option>
                <option value="special_offer">عرض خاص</option>
                <option value="seasonal">موسمي</option>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="نسبة الخصم"
                value={ruleData.discount_percentage}
                onChange={(e) =>
                  setRuleData({
                    ...ruleData,
                    discount_percentage: Number(e.target.value)
                  })
                }
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>
                }}
              />
            </Grid>

            {ruleData.rule_type === 'quantity' && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="الحد الأدنى للكمية"
                  value={ruleData.min_quantity}
                  onChange={(e) =>
                    setRuleData({
                      ...ruleData,
                      min_quantity: Number(e.target.value)
                    })
                  }
                />
              </Grid>
            )}

            {ruleData.rule_type === 'special_offer' && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="الحد الأدنى للمبلغ"
                  value={ruleData.min_amount}
                  onChange={(e) =>
                    setRuleData({
                      ...ruleData,
                      min_amount: Number(e.target.value)
                    })
                  }
                />
              </Grid>
            )}

            {ruleData.rule_type === 'customer_type' && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="نوع العميل"
                  value={ruleData.customer_type}
                  onChange={(e) =>
                    setRuleData({
                      ...ruleData,
                      customer_type: e.target.value
                    })
                  }
                  SelectProps={{ native: true }}
                >
                  <option value="">اختر نوع العميل</option>
                  <option value="regular">عادي</option>
                  <option value="vip">VIP</option>
                  <option value="wholesale">جملة</option>
                  <option value="distributor">موزع</option>
                </TextField>
              </Grid>
            )}

            {(ruleData.rule_type === 'seasonal' ||
              ruleData.rule_type === 'special_offer') && (
              <>
                <Grid item xs={12} md={6}>
                  <DatePicker
                    label="تاريخ البداية"
                    value={ruleData.start_date}
                    onChange={(date) =>
                      setRuleData({ ...ruleData, start_date: date })
                    }
                    slotProps={{ textField: { fullWidth: true } }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <DatePicker
                    label="تاريخ النهاية"
                    value={ruleData.end_date}
                    onChange={(date) =>
                      setRuleData({ ...ruleData, end_date: date })
                    }
                    slotProps={{ textField: { fullWidth: true } }}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={testMutation.isLoading}
              >
                {testMutation.isLoading ? (
                  <CircularProgress size={24} />
                ) : (
                  'اختبار القاعدة'
                )}
              </Button>
            </Grid>
          </Grid>
        </form>

        {testMutation.isSuccess && (
          <Box mt={3}>
            {testMutation.data.data.is_applicable ? (
              <Alert severity="success">
                <Typography variant="subtitle1" gutterBottom>
                  القاعدة منطبقة على الطلب
                </Typography>
                <Typography>
                  السعر الحالي: {formatCurrency(testMutation.data.data.current_price!)}
                </Typography>
                <Typography>
                  السعر بعد الخصم: {formatCurrency(testMutation.data.data.test_price!)}
                </Typography>
                <Typography>
                  مبلغ الخصم: {formatCurrency(testMutation.data.data.discount_amount!)}
                </Typography>
              </Alert>
            ) : (
              <Alert severity="info">
                {testMutation.data.data.reason || 'القاعدة غير منطبقة على الطلب'}
              </Alert>
            )}
          </Box>
        )}

        {testMutation.isError && (
          <Box mt={3}>
            <Alert severity="error">
              حدث خطأ أثناء اختبار القاعدة. يرجى المحاولة مرة أخرى.
            </Alert>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};