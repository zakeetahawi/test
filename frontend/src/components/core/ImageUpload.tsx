import { FC, useState, useRef } from 'react';
import {
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNotification } from './NotificationProvider';

interface ImageUploadProps {
  value?: string;
  onChange: (file: File | null) => void;
  onDelete?: () => void;
  maxSize?: number; // بالبايت
  accept?: string;
  aspectRatio?: number;
  loading?: boolean;
}

const ImageUpload: FC<ImageUploadProps> = ({
  value,
  onChange,
  onDelete,
  maxSize = 5 * 1024 * 1024, // 5 ميجابايت افتراضياً
  accept = 'image/*',
  aspectRatio,
  loading = false,
}) => {
  const { t } = useTranslation();
  const { showError } = useNotification();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(value || null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (file: File | null) => {
    if (!file) {
      setPreviewUrl(null);
      onChange(null);
      return;
    }

    // التحقق من نوع الملف
    if (!file.type.startsWith('image/')) {
      showError(t('error_invalid_image_type'));
      return;
    }

    // التحقق من حجم الملف
    if (file.size > maxSize) {
      showError(
        t('error_file_too_large', {
          size: Math.round(maxSize / (1024 * 1024)),
        })
      );
      return;
    }

    // إنشاء معاينة للصورة
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      
      // التحقق من أبعاد الصورة إذا كان مطلوباً
      if (aspectRatio) {
        const img = new Image();
        img.onload = () => {
          const actualRatio = img.width / img.height;
          if (Math.abs(actualRatio - aspectRatio) > 0.1) {
            showError(t('error_invalid_aspect_ratio'));
            return;
          }
          setPreviewUrl(dataUrl);
          onChange(file);
        };
        img.src = dataUrl;
      } else {
        setPreviewUrl(dataUrl);
        onChange(file);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileChange(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <Paper
      sx={{
        position: 'relative',
        width: '100%',
        height: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        border: (theme) =>
          isDragging
            ? `2px dashed ${theme.palette.primary.main}`
            : '2px dashed rgba(0, 0, 0, 0.12)',
        bgcolor: isDragging ? 'action.hover' : 'background.paper',
        overflow: 'hidden',
      }}
      onClick={() => fileInputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
        style={{ display: 'none' }}
      />

      {loading ? (
        <CircularProgress />
      ) : previewUrl ? (
        <>
          <Box
            component="img"
            src={previewUrl}
            alt="Preview"
            sx={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
            }}
          />
          {onDelete && (
            <IconButton
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                bgcolor: 'background.paper',
                '&:hover': {
                  bgcolor: 'error.light',
                  color: 'common.white',
                },
              }}
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              <DeleteIcon />
            </IconButton>
          )}
        </>
      ) : (
        <Box sx={{ textAlign: 'center' }}>
          <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
          <Typography variant="body1" color="textSecondary">
            {t('drop_image_here')}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {t('or_click_to_upload')}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ImageUpload;