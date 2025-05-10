import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Container, Paper, Typography, Breadcrumbs, Link } from '@mui/material';
import { useTranslation } from 'react-i18next';
import InstallationTracker from '../../components/installations/InstallationTracker';

const InstallationPage: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return (
      <Container>
        <Typography color="error">
          {t('معرف التركيب غير صالح')}
        </Typography>
      </Container>
    );
  }

  return (
    <Container>
      {/* مسار التنقل */}
      <Breadcrumbs sx={{ my: 2 }}>
        <Link color="inherit" href="/installations">
          {t('التركيبات')}
        </Link>
        <Typography color="textPrimary">
          {t('تتبع التركيب')} #{id}
        </Typography>
      </Breadcrumbs>

      {/* عنوان الصفحة */}
      <Typography variant="h4" gutterBottom>
        {t('تتبع التركيب')} #{id}
      </Typography>

      {/* متتبع التركيب */}
      <Paper elevation={2}>
        <InstallationTracker installationId={parseInt(id)} />
      </Paper>
    </Container>
  );
};

export default InstallationPage;
