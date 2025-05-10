import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  Typography,
  Chip,
  Box
} from '@mui/material';
import { useTranslation } from 'react-i18next';

interface Task {
  id: number;
  title: string;
  priority: 'high' | 'medium' | 'low';
  dueDate: string;
  completed: boolean;
}

interface Props {
  tasks: Task[];
}

const TasksList: React.FC<Props> = ({ tasks }) => {
  const { t } = useTranslation();

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <List>
      {tasks.map((task) => (
        <ListItem
          key={task.id}
          dense
          divider
          sx={{
            opacity: task.completed ? 0.7 : 1,
            transition: 'opacity 0.2s'
          }}
        >
          <ListItemIcon>
            <Checkbox
              edge="start"
              checked={task.completed}
              tabIndex={-1}
              disableRipple
            />
          </ListItemIcon>
          <ListItemText
            primary={
              <Typography
                variant="body2"
                sx={{
                  textDecoration: task.completed ? 'line-through' : 'none'
                }}
              >
                {task.title}
              </Typography>
            }
            secondary={
              <Box sx={{ mt: 0.5 }}>
                <Chip
                  label={t(`tasks.priority.${task.priority}`)}
                  color={getPriorityColor(task.priority) as any}
                  size="small"
                  sx={{ mr: 1 }}
                />
                <Typography
                  variant="caption"
                  component="span"
                  color="textSecondary"
                >
                  {new Date(task.dueDate).toLocaleDateString('ar-IL')}
                </Typography>
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  );
};

export default TasksList;