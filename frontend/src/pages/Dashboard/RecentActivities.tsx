import React from 'react';
import { List, ListItem, ListItemText, ListItemIcon, Typography, Divider } from '@mui/material';
import { useTranslation } from 'react-i18next';
import PersonIcon from '@mui/icons-material/Person';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import InventoryIcon from '@mui/icons-material/Inventory';
import FactoryIcon from '@mui/icons-material/Factory';

// سيتم استبدال هذا لاحقاً بجلب البيانات من API
const mockActivities = [
  {
    id: 1,
    type: 'customer',
    message: 'dashboard.activity.new_customer',
    time: '10:30',
    icon: PersonIcon,
  },
  {
    id: 2,
    type: 'order',
    message: 'dashboard.activity.new_order',
    time: '09:45',
    icon: ShoppingCartIcon,
  },
  {
    id: 3,
    type: 'inventory',
    message: 'dashboard.activity.low_stock',
    time: '09:15',
    icon: InventoryIcon,
  },
  {
    id: 4,
    type: 'factory',
    message: 'dashboard.activity.production_complete',
    time: '08:30',
    icon: FactoryIcon,
  },
];

const RecentActivities: React.FC = () => {
  const { t } = useTranslation();

  return (
    <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
      {mockActivities.map((activity, index) => (
        <React.Fragment key={activity.id}>
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <activity.icon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t(activity.message)}
              secondary={
                <Typography
                  sx={{ display: 'inline' }}
                  component="span"
                  variant="body2"
                  color="text.secondary"
                >
                  {activity.time}
                </Typography>
              }
            />
          </ListItem>
          {index < mockActivities.length - 1 && <Divider variant="inset" component="li" />}
        </React.Fragment>
      ))}
    </List>
  );
};

export default RecentActivities;