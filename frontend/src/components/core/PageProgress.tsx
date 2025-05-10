import { FC, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { LinearProgress } from '@mui/material';

const PageProgress: FC = () => {
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500); // إخفاء شريط التقدم بعد نصف ثانية

    return () => {
      clearTimeout(timer);
    };
  }, [location.pathname]);

  if (!isLoading) return null;

  return (
    <LinearProgress
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: (theme) => theme.zIndex.appBar + 1,
      }}
    />
  );
};

export default PageProgress;