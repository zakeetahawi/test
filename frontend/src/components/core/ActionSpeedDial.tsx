import { FC } from 'react';
import {
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  useTheme,
  Box,
} from '@mui/material';
import { SvgIconComponent } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface Action {
  icon: SvgIconComponent;
  name: string;
  onClick: () => void;
}

interface ActionSpeedDialProps {
  actions: Action[];
  position?: {
    top?: number;
    right?: number;
    bottom?: number;
    left?: number;
  };
}

const ActionSpeedDial: FC<ActionSpeedDialProps> = ({
  actions,
  position = { bottom: 16, right: 16 },
}) => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        position: 'fixed',
        ...position,
        zIndex: theme.zIndex.speedDial,
      }}
    >
      <SpeedDial
        ariaLabel={t('quick_actions')}
        icon={<SpeedDialIcon />}
        direction="up"
      >
        {actions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={<action.icon />}
            tooltipTitle={action.name}
            onClick={action.onClick}
          />
        ))}
      </SpeedDial>
    </Box>
  );
};

export default ActionSpeedDial;