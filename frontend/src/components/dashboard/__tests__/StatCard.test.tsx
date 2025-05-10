import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from '../StatCard';
import { People as PeopleIcon } from '@mui/icons-material';

describe('StatCard', () => {
  const defaultProps = {
    title: 'العملاء',
    value: 100,
    icon: <PeopleIcon />,
  };

  it('renders title and value correctly', () => {
    render(<StatCard {...defaultProps} />);
    
    expect(screen.getByText('العملاء')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders trend indicator when trend is provided', () => {
    render(
      <StatCard
        {...defaultProps}
        trend={{
          value: 15,
          isPositive: true,
        }}
      />
    );

    const trendElement = screen.getByText((content, element) => {
      return element?.textContent === '▲ 15%';
    });
    expect(trendElement).toBeInTheDocument();
  });

  it('shows negative trend correctly', () => {
    render(
      <StatCard
        {...defaultProps}
        trend={{
          value: 10,
          isPositive: false,
        }}
      />
    );
    
    const trendElement = screen.getByText((content, element) => {
      return element?.textContent === '▼ 10%';
    });
    expect(trendElement).toBeInTheDocument();
  });
});