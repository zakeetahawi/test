import React from 'react';
import {
  Box,
  Paper,
  Grid,
  Typography,
  Chip,
  Button,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  TextField,
  Card,
  CardContent
} from '@mui/material';
import {
  Edit as EditIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  LocationOn as LocationIcon,
  Delete as DeleteIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { CustomerType } from '../../types/customer';
import { useNavigate } from 'react-router-dom';

interface CustomerDetailsProps {
  customer: CustomerType;
  onAddNote: (note: string) => Promise<void>;
  onDelete: () => Promise<void>;
}

export const CustomerDetails: React.FC<CustomerDetailsProps> = ({
  customer,
  onAddNote,
  onDelete
}) => {
  const navigate = useNavigate();
  const [newNote, setNewNote] = React.useState('');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'blocked':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleAddNote = async () => {
    if (newNote.trim()) {
      await onAddNote(newNote);
      setNewNote('');
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        {/* رأس الصفحة */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar
              src={customer.image}
              sx={{ width: 100, height: 100 }}
            />
            <Box>
              <Typography variant="h5">
                {customer.name}
                <Typography component="span" color="text.secondary" sx={{ ml: 1 }}>
                  ({customer.code})
                </Typography>
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Chip
                  label={customer.status === 'active' ? 'نشط' : 
                         customer.status === 'inactive' ? 'غير نشط' : 'محظور'}
                  color={getStatusColor(customer.status) as any}
                  size="small"
                  sx={{ mr: 1 }}
                />
                <Chip
                  label={customer.customer_type === 'individual' ? 'فرد' : 
                         customer.customer_type === 'company' ? 'شركة' : 'حكومي'}
                  variant="outlined"
                  size="small"
                />
              </Box>
            </Box>
          </Box>
          <Box>
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => navigate(\`/customers/\${customer.id}/edit\`)}
              sx={{ ml: 1 }}
            >
              تعديل
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={onDelete}
            >
              حذف
            </Button>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* معلومات الاتصال */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  معلومات الاتصال
                </Typography>
                <List>
                  <ListItem>
                    <PhoneIcon sx={{ ml: 2 }} />
                    <ListItemText
                      primary="رقم الهاتف"
                      secondary={customer.phone}
                      secondaryTypographyProps={{ dir: 'ltr' }}
                    />
                  </ListItem>
                  {customer.email && (
                    <ListItem>
                      <EmailIcon sx={{ ml: 2 }} />
                      <ListItemText
                        primary="البريد الإلكتروني"
                        secondary={customer.email}
                        secondaryTypographyProps={{ dir: 'ltr' }}
                      />
                    </ListItem>
                  )}
                  {customer.address && (
                    <ListItem>
                      <LocationIcon sx={{ ml: 2 }} />
                      <ListItemText
                        primary="العنوان"
                        secondary={customer.address}
                      />
                    </ListItem>
                  )}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  معلومات أخرى
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="الفرع"
                      secondary={customer.branch.name}
                    />
                  </ListItem>
                  {customer.category && (
                    <ListItem>
                      <ListItemText
                        primary="التصنيف"
                        secondary={customer.category.name}
                      />
                    </ListItem>
                  )}
                  <ListItem>
                    <ListItemText
                      primary="تاريخ التسجيل"
                      secondary={new Date(customer.created_at).toLocaleDateString('ar-EG')}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* قسم الملاحظات */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          الملاحظات
        </Typography>
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            placeholder="أضف ملاحظة جديدة..."
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
          />
          <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddNote}
              disabled={!newNote.trim()}
            >
              إضافة ملاحظة
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};