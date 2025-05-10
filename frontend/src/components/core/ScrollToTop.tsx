import { FC, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Fab, useScrollTrigger, Zoom, Box } from '@mui/material';
import { KeyboardArrowUp as KeyboardArrowUpIcon } from '@mui/icons-material';

interface ScrollToTopProps {
  threshold?: number;
}

const ScrollToTop: FC<ScrollToTopProps> = ({ threshold = 100 }) => {
  const { pathname } = useLocation();
  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold,
  });

  const handleClick = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  // التمرير إلى أعلى عند تغيير المسار
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <Zoom in={trigger}>
      <Box
        role="presentation"
        sx={{
          position: 'fixed',
          bottom: (theme) => theme.spacing(2),
          right: (theme) => theme.spacing(2),
          zIndex: (theme) => theme.zIndex.speedDial,
        }}
      >
        <Fab
          color="primary"
          size="small"
          aria-label="scroll back to top"
          onClick={handleClick}
        >
          <KeyboardArrowUpIcon />
        </Fab>
      </Box>
    </Zoom>
  );
};

export default ScrollToTop;