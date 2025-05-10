import React from 'react';
import { render, screen, fireEvent } from '@/utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import LoadingButton from './LoadingButton';

describe('LoadingButton', () => {
  it('renders children correctly', () => {
    render(<LoadingButton>انقر هنا</LoadingButton>);
    expect(screen.getByText('انقر هنا')).toBeInTheDocument();
  });

  it('shows loading spinner when loading prop is true', () => {
    render(<LoadingButton loading>جاري التحميل</LoadingButton>);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByText('جاري التحميل')).toBeInTheDocument();
  });

  it('hides the loading spinner when loading is false', () => {
    render(<LoadingButton loading={false}>جاهز</LoadingButton>);
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('is disabled when loading', () => {
    render(<LoadingButton loading>جاري المعالجة</LoadingButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is disabled when disabled prop is true', () => {
    render(<LoadingButton disabled>معطل</LoadingButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(
      <LoadingButton onClick={handleClick}>انقر هنا</LoadingButton>
    );
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('positions loading spinner correctly based on loadingPosition prop', () => {
    const { rerender } = render(
      <LoadingButton loading loadingPosition="start">اختبار</LoadingButton>
    );
    let spinner = screen.getByRole('progressbar');
    expect(spinner.parentElement).toHaveStyle({ left: '16px' });

    rerender(
      <LoadingButton loading loadingPosition="end">اختبار</LoadingButton>
    );
    spinner = screen.getByRole('progressbar');
    expect(spinner.parentElement).toHaveStyle({ right: '16px' });

    rerender(
      <LoadingButton loading loadingPosition="center">اختبار</LoadingButton>
    );
    spinner = screen.getByRole('progressbar');
    expect(spinner.parentElement).toHaveStyle({ width: '100%' });
  });

  it('renders with custom progress size', () => {
    const customSize = 32;
    render(
      <LoadingButton loading progressSize={customSize}>اختبار</LoadingButton>
    );
    const spinner = screen.getByRole('progressbar');
    expect(spinner).toHaveStyle({ width: `${customSize}px`, height: `${customSize}px` });
  });

  it('applies custom styles through sx prop', () => {
    render(
      <LoadingButton sx={{ backgroundColor: 'rgb(0, 255, 0)' }}>
        زر مخصص
      </LoadingButton>
    );
    expect(screen.getByRole('button')).toHaveStyle({ backgroundColor: 'rgb(0, 255, 0)' });
  });

  it('preserves other Button props', () => {
    render(
      <LoadingButton
        variant="contained"
        color="secondary"
        size="large"
        fullWidth
      >
        زر كامل العرض
      </LoadingButton>
    );
    const button = screen.getByRole('button');
    expect(button).toHaveClass('MuiButton-contained');
    expect(button).toHaveClass('MuiButton-colorSecondary');
    expect(button).toHaveClass('MuiButton-sizeLarge');
    expect(button).toHaveClass('MuiButton-fullWidth');
  });

  it('handles RTL layout correctly', () => {
    const { container } = render(
      <LoadingButton loading loadingPosition="start">اختبار RTL</LoadingButton>
    );
    expect(container.firstChild).toHaveStyle({ direction: 'rtl' });
  });

  it('prevents clicking when loading', () => {
    const handleClick = vi.fn();
    render(
      <LoadingButton loading onClick={handleClick}>
        جاري المعالجة
      </LoadingButton>
    );
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });
});
