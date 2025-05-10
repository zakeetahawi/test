import { useState, useCallback } from 'react';
import { useAppDispatch } from './redux';
import { showNotification } from '../store/slices/uiSlice';

interface UseAsyncOperationOptions {
  successMessage?: string;
  errorMessage?: string;
  showSuccessNotification?: boolean;
  showErrorNotification?: boolean;
}

export const useAsyncOperation = <T>(
  operation: () => Promise<T>,
  options: UseAsyncOperationOptions = {}
) => {
  const {
    successMessage = 'تمت العملية بنجاح',
    errorMessage = 'حدث خطأ أثناء تنفيذ العملية',
    showSuccessNotification = true,
    showErrorNotification = true
  } = options;

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const dispatch = useAppDispatch();

  const execute = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await operation();
      
      if (showSuccessNotification) {
        dispatch(showNotification({
          message: successMessage,
          type: 'success'
        }));
      }
      
      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : errorMessage;
      setError(err as Error);
      
      if (showErrorNotification) {
        dispatch(showNotification({
          message: errorMsg,
          type: 'error'
        }));
      }
      
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [operation, successMessage, errorMessage, showSuccessNotification, showErrorNotification, dispatch]);

  return {
    execute,
    isLoading,
    error,
    reset: () => setError(null)
  };
};