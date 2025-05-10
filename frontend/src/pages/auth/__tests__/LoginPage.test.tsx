import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import authReducer, { login } from '../../../store/slices/authSlice';
import { LoginPage } from '../LoginPage';

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer
    },
    preloadedState: {
      auth: {
        isAuthenticated: false,
        tokens: null,
        loading: false,
        error: null,
        ...initialState
      }
    }
  });
};

describe('LoginPage', () => {
  const renderLoginPage = (initialState = {}) => {
    const store = createMockStore(initialState);
    return render(
      <Provider store={store}>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </Provider>
    );
  };

  it('renders login form correctly', () => {
    renderLoginPage();
    
    expect(screen.getByLabelText(/اسم المستخدم/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/كلمة المرور/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /تسجيل الدخول/i })).toBeInTheDocument();
  });

  it('shows error message when login fails', async () => {
    const errorMessage = 'فشل تسجيل الدخول';
    renderLoginPage({ error: errorMessage });
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('updates input values on change', () => {
    renderLoginPage();
    
    const usernameInput = screen.getByLabelText(/اسم المستخدم/i);
    const passwordInput = screen.getByLabelText(/كلمة المرور/i);
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('password123');
  });

  it('disables submit button while loading', () => {
    renderLoginPage({ loading: true });
    
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText('جاري التحميل...')).toBeInTheDocument();
  });
});