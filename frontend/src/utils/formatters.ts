import { format } from 'date-fns';
import { ar } from 'date-fns/locale';

// تنسيق الأرقام بالنمط العربي
export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('ar-SA').format(value);
};

// تنسيق العملة (ريال سعودي)
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ar-SA', {
    style: 'currency',
    currency: 'SAR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

// تنسيق التاريخ بالنمط العربي
export const formatDate = (date: string | Date): string => {
  if (!date) return '';
  return format(new Date(date), 'PPpp', { locale: ar });
};

// تنسيق التاريخ والوقت بالنمط العربي
export const formatDateTime = (date: string | Date): string => {
  return new Intl.DateTimeFormat('ar-SA', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
};

// تنسيق النسبة المئوية
export const formatPercentage = (value: number): string => {
  return new Intl.NumberFormat('ar-SA', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
};

// تنسيق الأرقام مع الوحدات
export const formatNumberWithUnit = (value: number, unit: string): string => {
  return `${formatNumber(value)} ${unit}`;
};

// تنسيق المساحة
export const formatArea = (value: number): string => {
  return formatNumberWithUnit(value, 'م²');
};

// تنسيق الوزن
export const formatWeight = (value: number): string => {
  if (value >= 1000) {
    return formatNumberWithUnit(value / 1000, 'كجم');
  }
  return formatNumberWithUnit(value, 'جم');
};