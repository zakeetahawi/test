import React from 'react';
import { Box, Button, Card, CardContent, Chip, IconButton, Stack, Typography } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Edit as EditIcon, Delete as DeleteIcon, PlayArrow as PlayIcon, Stop as StopIcon } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { formatDate } from '../../utils/dateUtils';
import api from '../../services/api';

interface DynamicPricingRule {
  id: number;
  name: string;
  rule_type: string;
  discount_percentage: number;
  is_active: boolean;
  start_date: string | null;
  end_date: string | null;
  priority: number;
}

export const DynamicPricingList: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['dynamicPricingRules'],
    queryFn: () => api.get('/orders/api/dynamic-pricing/').then(res => res.data)
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (ruleId: number) => 
      api.post(`/orders/api/dynamic-pricing/${ruleId}/toggle_active/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dynamicPricingRules'] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (ruleId: number) => 
      api.delete(`/orders/api/dynamic-pricing/${ruleId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dynamicPricingRules'] });
    }
  });

  const columns: GridColDef[] = [
    { field: 'name', headerName: 'اسم القاعدة', flex: 1 },
    { 
      field: 'rule_type', 
      headerName: 'نوع القاعدة', 
      width: 130,
      renderCell: (params) => (
        <Chip 
          label={params.value === 'seasonal' ? 'موسمي' : 
                params.value === 'quantity' ? 'كمية' :
                params.value === 'customer_type' ? 'نوع العميل' : 'عرض خاص'}
          color={params.value === 'seasonal' ? 'primary' : 
                params.value === 'quantity' ? 'secondary' :
                params.value === 'customer_type' ? 'info' : 'success'}
          variant="outlined"
        />
      )
    },
    { 
      field: 'discount_percentage', 
      headerName: 'نسبة الخصم', 
      width: 120,
      renderCell: (params) => `${params.value}%`
    },
    { 
      field: 'is_active', 
      headerName: 'الحالة', 
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value ? 'مفعل' : 'معطل'}
          color={params.value ? 'success' : 'error'}
        />
      )
    },
    {
      field: 'actions',
      headerName: 'الإجراءات',
      width: 180,
      renderCell: (params) => (
        <Stack direction="row" spacing={1}>
          <IconButton
            size="small"
            onClick={() => toggleActiveMutation.mutate(params.row.id)}
            color={params.row.is_active ? 'error' : 'success'}
          >
            {params.row.is_active ? <StopIcon /> : <PlayIcon />}
          </IconButton>
          <IconButton 
            size="small" 
            onClick={() => {/* التوجيه لصفحة التعديل */}}
            color="primary"
          >
            <EditIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => {
              if (window.confirm('هل أنت متأكد من حذف هذه القاعدة؟')) {
                deleteMutation.mutate(params.row.id);
              }
            }}
            color="error"
          >
            <DeleteIcon />
          </IconButton>
        </Stack>
      )
    }
  ];

  return (
    <Box>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" component="h2">
              قواعد التسعير الديناميكي
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => {/* التوجيه لصفحة إضافة قاعدة جديدة */}}
            >
              إضافة قاعدة جديدة
            </Button>
          </Box>
          <Box style={{ height: 400, width: '100%' }}>
            <DataGrid
              rows={rules}
              columns={columns}
              loading={isLoading}
              disableRowSelectionOnClick
              pageSizeOptions={[5, 10, 25]}
              initialState={{
                pagination: { paginationModel: { pageSize: 10 } },
              }}
            />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};