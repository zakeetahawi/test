import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material';
import { Sidebar } from '../Sidebar';

const theme = createTheme({
  direction: 'rtl',
});

const renderSidebar = () => {
  return render(
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    </ThemeProvider>
  );
};

describe('Sidebar', () => {
  it('renders all main menu items', () => {
    renderSidebar();
    
    expect(screen.getByText('لوحة التحكم')).toBeInTheDocument();
    expect(screen.getByText('العملاء')).toBeInTheDocument();
    expect(screen.getByText('المخزون')).toBeInTheDocument();
    expect(screen.getByText('الطلبات')).toBeInTheDocument();
    expect(screen.getByText('التفتيش')).toBeInTheDocument();
    expect(screen.getByText('التركيب')).toBeInTheDocument();
  });

  it('expands submenu when parent item is clicked', () => {
    renderSidebar();
    
    const inventoryItem = screen.getByText('المخزون');
    fireEvent.click(inventoryItem);
    
    expect(screen.getByText('المنتجات')).toBeInTheDocument();
    expect(screen.getByText('المستودعات')).toBeInTheDocument();
  });

  it('collapses submenu when parent item is clicked again', () => {
    renderSidebar();
    
    const inventoryItem = screen.getByText('المخزون');
    fireEvent.click(inventoryItem); // Expand
    fireEvent.click(inventoryItem); // Collapse
    
    expect(screen.queryByText('المنتجات')).not.toBeInTheDocument();
    expect(screen.queryByText('المستودعات')).not.toBeInTheDocument();
  });
});