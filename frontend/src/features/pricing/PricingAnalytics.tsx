import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  Alert,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineOppositeContent,
  TimelineSeparator,
  TimelineConnector,
  TimelineDot,
  TimelineContent
} from '@mui/lab';
import { DatePicker } from '@mui/x-date-pickers';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Check as CheckIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

interface PricingSuggestion {
  rule_id: number;
  rule_name: string;
  suggestion: string;
  reason: string;
  current_discount?: number;
  suggested_discount?: number;
}

interface RuleSummary {
  name: string;
  orders_count: number;
  total_discount: number;
  total_revenue: number;
}

export const PricingAnalytics: React.FC = () => {
  const [startDate, setStartDate] = useState<Date | null>(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  );
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [selectedRule, setSelectedRule] = useState<PricingSuggestion | null>(null);
  
  const queryClient = useQueryClient();

  const { data: analytics, isLoading } = useQuery<{
    report: {
      total_orders: number;
      total_revenue: number;
      total_discount: number;
      rules_summary: Record<string, RuleSummary>;
    };
    suggestions: PricingSuggestion[];
  }>({
    queryKey: ['pricingAnalytics', startDate, endDate],
    queryFn: () =>
      api.get('/orders/api/dynamic-pricing/analytics/', {
        params: {
          start_date: startDate?.toISOString(),
          end_date: endDate?.toISOString()
        }
      }).then(res => res.data)
  });

  const applySuggestionMutation = useMutation({
    mutationFn: (suggestion: PricingSuggestion) =>
      api.post(`/orders/api/dynamic-pricing/${suggestion.rule_id}/apply_suggestion/`, {
        suggested_discount: suggestion.suggested_discount
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pricingAnalytics'] });
      setSelectedRule(null);
    }
  });

  const handleApplySuggestion = () => {
    if (selectedRule) {
      applySuggestionMutation.mutate(selectedRule);
    }
  };

  if (isLoading) {
    return <Alert severity="info">جاري تحميل التحليلات...</Alert>;
  }

  const { report, suggestions } = analytics || {};

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6">فترة التحليل</Typography>
                <Box display="flex" gap={2}>
                  <DatePicker
                    label="من تاريخ"
                    value={startDate}
                    onChange={setStartDate}
                    slotProps={{ textField: { size: 'small' } }}
                  />
                  <DatePicker
                    label="إلى تاريخ"
                    value={endDate}
                    onChange={setEndDate}
                    slotProps={{ textField: { size: 'small' } }}
                  />
                </Box>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        إجمالي الطلبات
                      </Typography>
                      <Typography variant="h4">
                        {report?.total_orders || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        إجمالي الإيرادات
                      </Typography>
                      <Typography variant="h4">
                        {formatCurrency(report?.total_revenue || 0)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        إجمالي الخصومات
                      </Typography>
                      <Typography variant="h4" color="error">
                        {formatCurrency(report?.total_discount || 0)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ملخص القواعد
              </Typography>
              <Timeline>
                {report?.rules_summary &&
                  Object.entries(report.rules_summary).map(([id, rule]) => (
                    <TimelineItem key={id}>
                      <TimelineOppositeContent color="text.secondary">
                        {rule.orders_count} طلب
                      </TimelineOppositeContent>
                      <TimelineSeparator>
                        <TimelineDot color={rule.total_revenue > 0 ? 'success' : 'error'}>
                          {rule.total_revenue > 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
                        </TimelineDot>
                        <TimelineConnector />
                      </TimelineSeparator>
                      <TimelineContent>
                        <Typography>{rule.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          الإيرادات: {formatCurrency(rule.total_revenue)}
                          <br />
                          الخصومات: {formatCurrency(rule.total_discount)}
                        </Typography>
                      </TimelineContent>
                    </TimelineItem>
                  ))}
              </Timeline>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                المقترحات
              </Typography>
              {suggestions?.length === 0 ? (
                <Alert severity="success">
                  لا توجد مقترحات للتحسين حالياً
                </Alert>
              ) : (
                suggestions?.map((suggestion: PricingSuggestion) => (
                  <Box
                    key={suggestion.rule_id}
                    mb={2}
                    p={2}
                    bgcolor="background.default"
                    borderRadius={1}
                  >
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle1">{suggestion.rule_name}</Typography>
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => setSelectedRule(suggestion)}
                      >
                        <CheckIcon />
                      </IconButton>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {suggestion.reason}
                    </Typography>
                    {suggestion.current_discount && (
                      <Box display="flex" gap={1} mt={1}>
                        <Chip
                          label={`${suggestion.current_discount}%`}
                          size="small"
                          color="default"
                        />
                        <TrendingUpIcon fontSize="small" color="action" />
                        <Chip
                          label={`${suggestion.suggested_discount}%`}
                          size="small"
                          color="primary"
                        />
                      </Box>
                    )}
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={Boolean(selectedRule)} onClose={() => setSelectedRule(null)}>
        <DialogTitle>تطبيق المقترح</DialogTitle>
        <DialogContent>
          <Typography>
            هل تريد تطبيق التعديل المقترح على قاعدة "{selectedRule?.rule_name}"؟
            {selectedRule?.suggested_discount && (
              <Typography color="primary" mt={1}>
                سيتم تغيير نسبة الخصم من {selectedRule.current_discount}% إلى{' '}
                {selectedRule.suggested_discount}%
              </Typography>
            )}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedRule(null)}>إلغاء</Button>
          <Button
            onClick={handleApplySuggestion}
            color="primary"
            variant="contained"
            disabled={applySuggestionMutation.isLoading}
          >
            تطبيق
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};