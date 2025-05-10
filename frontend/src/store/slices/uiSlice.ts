import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationState {
  message: string;
  type: NotificationType;
  open: boolean;
}

interface UIState {
  notification: NotificationState;
  isLoading: boolean;
}

const initialState: UIState = {
  notification: {
    message: '',
    type: 'info',
    open: false
  },
  isLoading: false
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    showNotification: (state, action: PayloadAction<{ message: string; type: NotificationType }>) => {
      state.notification = {
        message: action.payload.message,
        type: action.payload.type,
        open: true
      };
    },
    hideNotification: (state) => {
      state.notification.open = false;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    }
  }
});

export const { showNotification, hideNotification, setLoading } = uiSlice.actions;
export default uiSlice.reducer;