import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

interface NoDataProps {
    message?: string;
    actionLabel?: string;
    onAction?: () => void;
}

export const NoData: React.FC<NoDataProps> = ({
    message = 'لا توجد بيانات للعرض',
    actionLabel,
    onAction,
}) => {
    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '200px',
                p: 3,
                textAlign: 'center',
            }}
        >
            <Typography variant="h6" color="text.secondary" gutterBottom>
                {message}
            </Typography>
            {actionLabel && onAction && (
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={onAction}
                    sx={{ mt: 2 }}
                >
                    {actionLabel}
                </Button>
            )}
        </Box>
    );
};