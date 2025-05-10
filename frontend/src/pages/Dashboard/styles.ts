import { Theme } from '@mui/material/styles';

export const dashboardStyles = (theme: Theme) => ({
  statCard: {
    height: '100%',
    transition: 'transform 0.3s ease-in-out',
    '&:hover': {
      transform: 'translateY(-5px)',
    },
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  cardContent: {
    padding: theme.spacing(3),
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing(2),
  },
  activityPaper: {
    borderRadius: '10px',
    height: '100%',
    overflow: 'hidden',
  },
  activityList: {
    maxHeight: 400,
    overflowY: 'auto',
    '&::-webkit-scrollbar': {
      width: '6px',
    },
    '&::-webkit-scrollbar-track': {
      background: theme.palette.background.default,
    },
    '&::-webkit-scrollbar-thumb': {
      background: theme.palette.primary.main,
      borderRadius: '3px',
    },
  },
  orderAmount: {
    color: theme.palette.success.main,
    fontWeight: 'bold',
  },
  growthIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing(0.5),
    marginTop: 'auto',
  },
});