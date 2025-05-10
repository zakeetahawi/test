import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material';
import { SnackbarProvider } from '@/components/core';

// Create test theme
export const testTheme = createTheme({
  direction: 'rtl',
  palette: {
    primary: {
      main: '#3f51b5',
    },
    secondary: {
      main: '#f50057',
    },
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

interface TestProvidersProps {
  children: React.ReactNode;
}

export const TestProviders: React.FC<TestProvidersProps> = ({ children }) => {
  return (
    <ThemeProvider theme={testTheme}>
      <SnackbarProvider>
        {children}
      </SnackbarProvider>
    </ThemeProvider>
  );
};

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) =>
  render(ui, {
    wrapper: TestProviders,
    ...options,
  });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Add custom matchers
expect.extend({
  toHaveComputedStyle(element: HTMLElement, property: string, value: string) {
    const computedStyle = window.getComputedStyle(element);
    const pass = computedStyle[property as keyof CSSStyleDeclaration] === value;

    return {
      pass,
      message: () =>
        `Expected element to have ${property}: ${value}. Got: ${computedStyle[property as keyof CSSStyleDeclaration]}`,
    };
  },
});

declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveComputedStyle(property: string, value: string): R;
    }
  }
}

// Test utils
export const mockConsoleError = () => {
  const originalError = console.error;
  beforeAll(() => {
    console.error = (...args: any[]) => {
      if (typeof args[0] === 'string' && args[0].includes('Warning:')) {
        return;
      }
      originalError.call(console, ...args);
    };
  });

  afterAll(() => {
    console.error = originalError;
  });
};

export const createMatchMedia = (width: number) => {
  return (query: string): MediaQueryList => ({
    matches: width >= parseInt(query.replace(/[^\d]/g, '')),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
  });
};
