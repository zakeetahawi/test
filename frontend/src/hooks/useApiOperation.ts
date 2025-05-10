import { useState, useCallback } from 'react';
import { useApi } from '../services/api';
import type { ApiError } from '../services/api';

interface UseApiOperationOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
  successMessage?: string;
}

interface ApiOperationState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
}

export function useApiOperation<T>(options: UseApiOperationOptions<T> = {}) {
  const [state, setState] = useState<ApiOperationState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const api = useApi();

  const execute = useCallback(
    async (
      operation: () => Promise<{ data: T }>,
      customSuccessMessage?: string
    ) => {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      try {
        const response = await operation();
        setState(prev => ({ ...prev, data: response.data, isLoading: false }));
        
        // Handle success
        if (options.onSuccess) {
          options.onSuccess(response.data);
        }
        
        // Show success message if provided
        const message = customSuccessMessage || options.successMessage;
        if (message) {
          api.handleSuccess(message);
        }
        
        return response.data;
      } catch (error) {
        const apiError = error as ApiError;
        setState(prev => ({ ...prev, error: apiError, isLoading: false }));
        
        // Handle error
        if (options.onError) {
          options.onError(apiError);
        }
        
        throw apiError;
      }
    },
    [api, options]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// Example usage:
/*
const MyComponent = () => {
  const { execute, isLoading, error } = useApiOperation<User>({
    successMessage: 'تم حفظ البيانات بنجاح',
    onSuccess: (data) => {
      // Handle success
    },
  });

  const handleSubmit = async (data: UserFormData) => {
    try {
      await execute(() => api.post('/users', data));
    } catch (error) {
      // Handle error
    }
  };

  return (
    <Button
      onClick={handleSubmit}
      disabled={isLoading}
    >
      {isLoading ? 'جاري الحفظ...' : 'حفظ'}
    </Button>
  );
};
*/
