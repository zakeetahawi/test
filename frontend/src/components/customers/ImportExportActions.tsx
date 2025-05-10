import React, { useRef } from 'react';
import { Button, Box } from '@mui/material';
import { Upload as UploadIcon, Download as DownloadIcon } from '@mui/icons-material';
import { CustomerService, CustomerFilters } from '../../services/customer.service';
import { useAppDispatch } from '../../hooks/redux';
import { showSnackbar } from '../../store/slices/snackbarSlice';

interface ImportExportActionsProps {
    filters: CustomerFilters;
    onImportSuccess: () => void;
}

export const ImportExportActions: React.FC<ImportExportActionsProps> = ({
    filters,
    onImportSuccess,
}) => {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const dispatch = useAppDispatch();

    const handleExport = async () => {
        try {
            const blob = await CustomerService.exportCustomers(filters);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `customers-export-${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء تصدير بيانات العملاء',
                    severity: 'error',
                })
            );
        }
    };

    const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            await CustomerService.importCustomers(file);
            dispatch(
                showSnackbar({
                    message: 'تم استيراد بيانات العملاء بنجاح',
                    severity: 'success',
                })
            );
            onImportSuccess();
        } catch (error) {
            dispatch(
                showSnackbar({
                    message: 'حدث خطأ أثناء استيراد بيانات العملاء',
                    severity: 'error',
                })
            );
        } finally {
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <Box sx={{ display: 'flex', gap: 2 }}>
            <input
                type="file"
                accept=".xlsx,.xls,.csv"
                style={{ display: 'none' }}
                ref={fileInputRef}
                onChange={handleImport}
            />
            <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                onClick={() => fileInputRef.current?.click()}
            >
                استيراد
            </Button>
            <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleExport}
            >
                تصدير
            </Button>
        </Box>
    );
};