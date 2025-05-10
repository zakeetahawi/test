import { FC, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
  PictureAsPdf as PdfIcon,
  Image as ImageIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNotification } from './NotificationProvider';
import { formatFileSize } from '@utils/formatters';

interface FileUploadProps {
  files: File[];
  onAdd: (files: File[]) => void;
  onRemove: (index: number) => void;
  maxSize?: number; // بالبايت
  accept?: string;
  maxFiles?: number;
  loading?: boolean;
}

const FileUpload: FC<FileUploadProps> = ({
  files,
  onAdd,
  onRemove,
  maxSize = 10 * 1024 * 1024, // 10 ميجابايت افتراضياً
  accept,
  maxFiles = 5,
  loading = false,
}) => {
  const { t } = useTranslation();
  const { showError } = useNotification();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (newFiles: FileList | null) => {
    if (!newFiles) return;

    const filesArray = Array.from(newFiles);
    const validFiles: File[] = [];
    const errors: string[] = [];

    // التحقق من عدد الملفات
    if (files.length + filesArray.length > maxFiles) {
      showError(t('error_max_files', { max: maxFiles }));
      return;
    }

    // التحقق من كل ملف
    filesArray.forEach((file) => {
      // التحقق من نوع الملف
      if (accept && !file.type.match(accept)) {
        errors.push(t('error_invalid_file_type', { name: file.name }));
        return;
      }

      // التحقق من حجم الملف
      if (file.size > maxSize) {
        errors.push(
          t('error_file_too_large', {
            name: file.name,
            size: Math.round(maxSize / (1024 * 1024)),
          })
        );
        return;
      }

      validFiles.push(file);
    });

    // عرض الأخطاء إن وجدت
    if (errors.length > 0) {
      errors.forEach((error) => showError(error));
    }

    // إضافة الملفات الصالحة
    if (validFiles.length > 0) {
      onAdd(validFiles);
    }
  };

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <ImageIcon />;
    if (fileType === 'application/pdf') return <PdfIcon />;
    return <FileIcon />;
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileChange(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <Box>
      <Paper
        sx={{
          p: 2,
          border: (theme) =>
            isDragging
              ? `2px dashed ${theme.palette.primary.main}`
              : '2px dashed rgba(0, 0, 0, 0.12)',
          bgcolor: isDragging ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          minHeight: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={accept}
          onChange={(e) => handleFileChange(e.target.files)}
          style={{ display: 'none' }}
        />

        <Box sx={{ textAlign: 'center' }}>
          <UploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
          <Typography variant="body1" color="textSecondary">
            {t('drop_files_here')}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {t('or_click_to_upload')}
          </Typography>
          {accept && (
            <Typography variant="caption" color="textSecondary" display="block">
              {t('accepted_files')}: {accept}
            </Typography>
          )}
          <Typography variant="caption" color="textSecondary" display="block">
            {t('max_file_size')}: {formatFileSize(maxSize)}
          </Typography>
        </Box>
      </Paper>

      {files.length > 0 && (
        <List>
          {files.map((file, index) => (
            <ListItem key={index}>
              <ListItemIcon>{getFileIcon(file.type)}</ListItemIcon>
              <ListItemText
                primary={file.name}
                secondary={formatFileSize(file.size)}
              />
              <ListItemSecondaryAction>
                {loading ? (
                  <CircularProgress size={24} />
                ) : (
                  <IconButton
                    edge="end"
                    onClick={() => onRemove(index)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                )}
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
};

export default FileUpload;