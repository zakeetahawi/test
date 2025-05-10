import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
    Box,
    Typography,
    Breadcrumbs,
    Link,
    Paper,
    Stack,
} from '@mui/material';
import { NavigateNext as NavigateNextIcon } from '@mui/icons-material';

interface BreadcrumbItem {
    label: string;
    path?: string;
}

interface PageHeaderProps {
    title: string;
    breadcrumbs?: BreadcrumbItem[];
    actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
    title,
    breadcrumbs = [],
    actions,
}) => {
    return (
        <Paper
            sx={{
                p: 3,
                mb: 3,
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                alignItems: { xs: 'stretch', sm: 'center' },
                gap: 2,
            }}
        >
            <Stack spacing={1}>
                <Typography variant="h5" component="h1">
                    {title}
                </Typography>
                {breadcrumbs.length > 0 && (
                    <Breadcrumbs
                        separator={<NavigateNextIcon fontSize="small" />}
                        aria-label="breadcrumb"
                    >
                        {breadcrumbs.map((item, index) => {
                            const isLast = index === breadcrumbs.length - 1;
                            return isLast ? (
                                <Typography
                                    key={item.label}
                                    color="text.primary"
                                >
                                    {item.label}
                                </Typography>
                            ) : (
                                <Link
                                    key={item.label}
                                    component={RouterLink}
                                    to={item.path || '#'}
                                    underline="hover"
                                    color="inherit"
                                >
                                    {item.label}
                                </Link>
                            );
                        })}
                    </Breadcrumbs>
                )}
            </Stack>
            {actions && <Box>{actions}</Box>}
        </Paper>
    );
};