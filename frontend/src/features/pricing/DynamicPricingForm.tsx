import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';

interface DynamicPricingFormData {
  id?: number;
  name: string;
  rule_type: 'seasonal' | 'quantity' | 'customer_type' | 'special_offer';
  discount_percentage: number;
  min_quantity?: number;
  min_amount?: number;
  customer_type?: string;
  start_date?: Date | null;
  end_date?: Date | null;
  priority: number;
  description?: string;
}

const schema = yup.object().shape({
  id: yup.number().optional(),
  name: yup.string().required('اسم القاعدة مطلوب'),
  rule_type: yup.mixed<DynamicPricingFormData['rule_type']>().required('نوع القاعدة مطلوب'),
  discount_percentage: yup
    .number()
    .min(0, 'يجب أن تكون النسبة أكبر من 0')
    .max(100, 'يجب أن تكون النسبة أقل من 100')
    .required('نسبة الخصم مطلوبة'),
  min_quantity: yup.number().when('rule_type', {
    is: 'quantity',
    then: (schema) => schema.required('الحد الأدنى للكمية مطلوب')
  }),
  min_amount: yup.number().when('rule_type', {
    is: 'special_offer',
    then: (schema) => schema.required('الحد الأدنى للمبلغ مطلوب')
  }),
  customer_type: yup.string().when('rule_type', {
    is: 'customer_type',
    then: (schema) => schema.required('نوع العميل مطلوب')
  }),
  start_date: yup.date().nullable().optional(),
  end_date: yup.date().nullable().optional(),
  priority: yup.number().required('الأولوية مطلوبة'),
  description: yup.string().optional()
});

interface Props {
  initialData?: Partial<DynamicPricingFormData>;
  onSuccess?: () => void;
}

export const DynamicPricingForm: React.FC<Props> = ({ initialData, onSuccess }) => {
  const queryClient = useQueryClient();
  const isEditMode = Boolean(initialData?.name);

  const { control, handleSubmit, watch, formState: { errors } } = useForm<DynamicPricingFormData>({
    resolver: yupResolver<DynamicPricingFormData>(schema),
    defaultValues: {
      name: initialData?.name || '',
      rule_type: initialData?.rule_type || 'seasonal',
      discount_percentage: initialData?.discount_percentage || 0,
      min_quantity: initialData?.min_quantity,
      min_amount: initialData?.min_amount,
      customer_type: initialData?.customer_type,
      start_date: initialData?.start_date ? new Date(initialData.start_date) : null,
      end_date: initialData?.end_date ? new Date(initialData.end_date) : null,
      priority: initialData?.priority || 0,
      description: initialData?.description || ''
    }
  });

  const mutation = useMutation({
    mutationFn: (data: DynamicPricingFormData) => {
      if (isEditMode && initialData?.id) {
        return api.put(`/orders/api/dynamic-pricing/${initialData.id}/`, data);
      }
      return api.post('/orders/api/dynamic-pricing/', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dynamicPricingRules'] });
      onSuccess?.();
    }
  });

  const ruleType = watch('rule_type');

  const onSubmit = (data: DynamicPricingFormData) => {
    mutation.mutate(data);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {isEditMode ? 'تعديل قاعدة التسعير' : 'إضافة قاعدة تسعير جديدة'}
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="اسم القاعدة"
                    fullWidth
                    error={Boolean(errors.name)}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="rule_type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth error={Boolean(errors.rule_type)}>
                    <InputLabel>نوع القاعدة</InputLabel>
                    <Select {...field} label="نوع القاعدة">
                      <MenuItem value="seasonal">موسمي</MenuItem>
                      <MenuItem value="quantity">كمية</MenuItem>
                      <MenuItem value="customer_type">نوع العميل</MenuItem>
                      <MenuItem value="special_offer">عرض خاص</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="discount_percentage"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label="نسبة الخصم"
                    fullWidth
                    error={Boolean(errors.discount_percentage)}
                    helperText={errors.discount_percentage?.message}
                  />
                )}
              />
            </Grid>

            {ruleType === 'quantity' && (
              <Grid item xs={12} md={6}>
                <Controller
                  name="min_quantity"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      type="number"
                      label="الحد الأدنى للكمية"
                      fullWidth
                      error={Boolean(errors.min_quantity)}
                      helperText={errors.min_quantity?.message}
                    />
                  )}
                />
              </Grid>
            )}

            {ruleType === 'special_offer' && (
              <Grid item xs={12} md={6}>
                <Controller
                  name="min_amount"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      type="number"
                      label="الحد الأدنى للمبلغ"
                      fullWidth
                      error={Boolean(errors.min_amount)}
                      helperText={errors.min_amount?.message}
                    />
                  )}
                />
              </Grid>
            )}

            {ruleType === 'customer_type' && (
              <Grid item xs={12} md={6}>
                <Controller
                  name="customer_type"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth error={Boolean(errors.customer_type)}>
                      <InputLabel>نوع العميل</InputLabel>
                      <Select {...field} label="نوع العميل">
                        <MenuItem value="regular">عادي</MenuItem>
                        <MenuItem value="vip">VIP</MenuItem>
                        <MenuItem value="wholesale">جملة</MenuItem>
                        <MenuItem value="distributor">موزع</MenuItem>
                      </Select>
                    </FormControl>
                  )}
                />
              </Grid>
            )}

            <Grid item xs={12} md={6}>
              <Controller
                name="start_date"
                control={control}
                render={({ field }) => (
                  <DateTimePicker
                    {...field}
                    label="تاريخ البداية"
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: Boolean(errors.start_date)
                      }
                    }}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="end_date"
                control={control}
                render={({ field }) => (
                  <DateTimePicker
                    {...field}
                    label="تاريخ النهاية"
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: Boolean(errors.end_date)
                      }
                    }}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="priority"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label="الأولوية"
                    fullWidth
                    error={Boolean(errors.priority)}
                    helperText={errors.priority?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="description"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="الوصف"
                    multiline
                    rows={4}
                    fullWidth
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Box display="flex" justifyContent="flex-end" gap={2}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={mutation.isLoading}
                >
                  {isEditMode ? 'تحديث' : 'إضافة'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};