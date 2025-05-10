import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardChart } from '../DashboardChart';

// تجاهل أخطاء Canvas في اختبارات Chart.js
vi.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="mock-line-chart" />,
  Bar: () => <div data-testid="mock-bar-chart" />,
}));

describe('DashboardChart', () => {
  const defaultProps = {
    title: 'عنوان الرسم البياني',
    data: {
      labels: ['يناير', 'فبراير', 'مارس'],
      data: [10, 20, 30],
    },
    type: 'line' as const,
  };

  it('renders chart title correctly', () => {
    render(<DashboardChart {...defaultProps} />);
    expect(screen.getByText('عنوان الرسم البياني')).toBeInTheDocument();
  });

  it('renders line chart when type is line', () => {
    render(<DashboardChart {...defaultProps} />);
    expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument();
  });

  it('renders bar chart when type is bar', () => {
    render(<DashboardChart {...{ ...defaultProps, type: 'bar' as const }} />);
    expect(screen.getByTestId('mock-bar-chart')).toBeInTheDocument();
  });
});