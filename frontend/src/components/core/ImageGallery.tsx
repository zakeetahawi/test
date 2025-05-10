import { FC, useState } from 'react';
import {
  ImageList,
  ImageListItem,
  Modal,
  IconButton,
  Box,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Close as CloseIcon,
  NavigateNext,
  NavigateBefore,
} from '@mui/icons-material';

interface Image {
  url: string;
  title: string;
}

interface ImageGalleryProps {
  images: Image[];
  cols?: number;
  gap?: number;
}

const ImageGallery: FC<ImageGalleryProps> = ({
  images,
  cols = 3,
  gap = 8,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [selectedImage, setSelectedImage] = useState<number | null>(null);

  const handleImageClick = (index: number) => {
    setSelectedImage(index);
  };

  const handleClose = () => {
    setSelectedImage(null);
  };

  const handlePrevious = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (selectedImage !== null) {
      setSelectedImage(selectedImage === 0 ? images.length - 1 : selectedImage - 1);
    }
  };

  const handleNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (selectedImage !== null) {
      setSelectedImage(selectedImage === images.length - 1 ? 0 : selectedImage + 1);
    }
  };

  return (
    <>
      <ImageList cols={isMobile ? 2 : cols} gap={gap}>
        {images.map((image, index) => (
          <ImageListItem
            key={index}
            onClick={() => handleImageClick(index)}
            sx={{ cursor: 'pointer' }}
          >
            <img
              src={image.url}
              alt={image.title}
              loading="lazy"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
          </ImageListItem>
        ))}
      </ImageList>

      <Modal
        open={selectedImage !== null}
        onClose={handleClose}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box
          sx={{
            position: 'relative',
            maxWidth: '90vw',
            maxHeight: '90vh',
            outline: 'none',
          }}
        >
          {selectedImage !== null && (
            <>
              <img
                src={images[selectedImage].url}
                alt={images[selectedImage].title}
                style={{
                  maxWidth: '100%',
                  maxHeight: '90vh',
                  objectFit: 'contain',
                }}
              />
              <IconButton
                onClick={handleClose}
                sx={{
                  position: 'absolute',
                  top: -40,
                  right: 0,
                  color: 'white',
                }}
              >
                <CloseIcon />
              </IconButton>
              {images.length > 1 && (
                <>
                  <IconButton
                    onClick={handlePrevious}
                    sx={{
                      position: 'absolute',
                      left: 16,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'white',
                      bgcolor: 'rgba(0, 0, 0, 0.3)',
                      '&:hover': {
                        bgcolor: 'rgba(0, 0, 0, 0.5)',
                      },
                    }}
                  >
                    <NavigateBefore />
                  </IconButton>
                  <IconButton
                    onClick={handleNext}
                    sx={{
                      position: 'absolute',
                      right: 16,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'white',
                      bgcolor: 'rgba(0, 0, 0, 0.3)',
                      '&:hover': {
                        bgcolor: 'rgba(0, 0, 0, 0.5)',
                      },
                    }}
                  >
                    <NavigateNext />
                  </IconButton>
                </>
              )}
            </>
          )}
        </Box>
      </Modal>
    </>
  );
};

export default ImageGallery;