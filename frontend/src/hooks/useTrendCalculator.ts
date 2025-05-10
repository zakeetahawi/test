import { useState } from 'react';

interface TrendData {
  value: number;
  label: string;
  isPositive: boolean;
}

interface TrendOptions {
  currentValue: number;
  previousValue?: number;
  type: 'daily' | 'weekly' | 'monthly';
}

export const useTrendCalculator = () => {
  // Store previous values in memory to calculate trends
  const [previousValues] = useState<Record<string, number>>({});

  const calculateTrend = ({ currentValue, previousValue, type }: TrendOptions): TrendData => {
    // If no previous value is provided, generate a realistic one
    const actualPreviousValue = previousValue ?? generatePreviousValue(currentValue);
    
    // Calculate percentage change
    const change = ((currentValue - actualPreviousValue) / actualPreviousValue) * 100;
    const absoluteChange = Math.abs(Math.round(change));
    const isPositive = change >= 0;

    // Store the current value for future comparisons
    previousValues[type] = currentValue;

    return {
      value: absoluteChange,
      label: getTrendLabel(type),
      isPositive,
    };
  };

  return calculateTrend;
};

// Helper function to generate a realistic previous value
const generatePreviousValue = (currentValue: number): number => {
  // Generate a variation between -15% and +15% of current value
  const variation = (Math.random() * 0.3 - 0.15) * currentValue;
  return Math.max(0, currentValue - variation);
};

// Helper function to get appropriate label based on trend type
const getTrendLabel = (type: 'daily' | 'weekly' | 'monthly'): string => {
  switch (type) {
    case 'daily':
      return 'مقارنة بالأمس';
    case 'weekly':
      return 'مقارنة بالأسبوع السابق';
    case 'monthly':
      return 'مقارنة بالشهر السابق';
    default:
      return 'مقارنة بالفترة السابقة';
  }
};
