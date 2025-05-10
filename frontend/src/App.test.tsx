import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from './theme/ThemeProvider';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import App from './App';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
    },
  },
});

const AppWithProviders = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </QueryClientProvider>
);

describe('App', () => {
  it('renders without crashing', () => {
    render(<AppWithProviders />);
  });

  it('shows login page when not authenticated', () => {
    render(<AppWithProviders />);
    expect(screen.getByRole('button', { name: /تسجيل الدخول/i })).toBeInTheDocument();
  });

  it('shows correct initial route', () => {
    render(<AppWithProviders />);
    expect(window.location.pathname).toBe('/');
  });

  // Add more test cases as needed
  it('displays the logo', () => {
    render(<AppWithProviders />);
    expect(screen.getByAltText('شعار النظام')).toBeInTheDocument();
  });

  it('has correct RTL direction', () => {
    render(<AppWithProviders />);
    const element = document.body;
    expect(element).toHaveStyle({ direction: 'rtl' });
  });
});
