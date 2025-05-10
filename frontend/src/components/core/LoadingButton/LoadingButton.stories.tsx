import type { Meta, StoryObj } from '@storybook/react';
import LoadingButton from './LoadingButton';
import { Save as SaveIcon, Send as SendIcon } from '@mui/icons-material';

const meta = {
  title: 'Core/LoadingButton',
  component: LoadingButton,
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'light',
    },
  },
  tags: ['autodocs'],
  args: {
    variant: 'contained',
    children: 'زر التحميل',
  },
} satisfies Meta<typeof LoadingButton>;

export default meta;
type Story = StoryObj<typeof meta>;

// Basic button
export const Basic: Story = {
  args: {
    children: 'انقر هنا',
  },
};

// Loading state
export const Loading: Story = {
  args: {
    loading: true,
    children: 'جاري التحميل',
  },
};

// Loading with position
export const LoadingStart: Story = {
  args: {
    loading: true,
    loadingPosition: 'start',
    children: 'جاري الحفظ',
    startIcon: <SaveIcon />,
  },
};

export const LoadingEnd: Story = {
  args: {
    loading: true,
    loadingPosition: 'end',
    children: 'جاري الإرسال',
    endIcon: <SendIcon />,
  },
};

export const LoadingCenter: Story = {
  args: {
    loading: true,
    loadingPosition: 'center',
    children: 'جاري المعالجة',
  },
};

// Variants
export const Contained: Story = {
  args: {
    variant: 'contained',
    children: 'زر رئيسي',
  },
};

export const Outlined: Story = {
  args: {
    variant: 'outlined',
    children: 'زر ثانوي',
  },
};

export const Text: Story = {
  args: {
    variant: 'text',
    children: 'زر نصي',
  },
};

// Colors
export const Primary: Story = {
  args: {
    color: 'primary',
    children: 'زر رئيسي',
  },
};

export const Secondary: Story = {
  args: {
    color: 'secondary',
    children: 'زر ثانوي',
  },
};

export const Error: Story = {
  args: {
    color: 'error',
    children: 'حذف',
  },
};

// Sizes
export const Small: Story = {
  args: {
    size: 'small',
    children: 'زر صغير',
  },
};

export const Medium: Story = {
  args: {
    size: 'medium',
    children: 'زر متوسط',
  },
};

export const Large: Story = {
  args: {
    size: 'large',
    children: 'زر كبير',
  },
};

// Full width
export const FullWidth: Story = {
  args: {
    fullWidth: true,
    children: 'زر كامل العرض',
  },
};

// Disabled
export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'زر معطل',
  },
};

// With icons
export const WithStartIcon: Story = {
  args: {
    startIcon: <SaveIcon />,
    children: 'حفظ',
  },
};

export const WithEndIcon: Story = {
  args: {
    endIcon: <SendIcon />,
    children: 'إرسال',
  },
};

// Custom size spinner
export const CustomSpinnerSize: Story = {
  args: {
    loading: true,
    progressSize: 16,
    children: 'تحميل مخصص',
  },
};
