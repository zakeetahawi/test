import { ButtonHTMLAttributes, FC, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

export const Button: FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <button 
      className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark disabled:opacity-50"
      {...props}
    >
      {children}
    </button>
  );
};