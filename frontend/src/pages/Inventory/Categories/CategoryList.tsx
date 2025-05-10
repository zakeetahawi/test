import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Chip,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { Category } from '@/types/inventory';
import { useTranslation } from 'react-i18next';

interface Props {
  categories: Category[];
  onEdit: (category: Category) => void;
  onDelete: (category: Category) => void;
}

const CategoryList: React.FC<Props> = ({ categories, onEdit, onDelete }) => {
  const { t } = useTranslation();

  return (
    <List>
      {categories.map((category) => (
        <ListItem key={category.id} divider>
          <ListItemText
            primary={category.name}
            secondary={
              <>
                <Typography variant="body2" color="textSecondary">
                  {category.description || t('inventory.no_description')}
                </Typography>
                <Chip
                  size="small"
                  label={t('inventory.products_count', { count: category.productsCount })}
                  sx={{ mt: 1 }}
                />
              </>
            }
          />
          <ListItemSecondaryAction>
            <IconButton
              edge="end"
              aria-label={t('edit')}
              onClick={() => onEdit(category)}
              size="small"
              sx={{ mr: 1 }}
            >
              <EditIcon />
            </IconButton>
            <IconButton
              edge="end"
              aria-label={t('delete')}
              onClick={() => onDelete(category)}
              size="small"
              disabled={category.productsCount > 0}
            >
              <DeleteIcon />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
      ))}
    </List>
  );
};

export default CategoryList;