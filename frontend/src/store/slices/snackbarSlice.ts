import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SnackbarState {
    open: boolean;
    message: string;
    severity: 'success' | 'info' | 'warning' | 'error';
}

const initialState: SnackbarState = {
    open: false,
    message: '',
    severity: 'info',
};

export const snackbarSlice = createSlice({
    name: 'snackbar',
    initialState,
    reducers: {
        showSnackbar: (
            state,
            action: PayloadAction<{ message: string; severity: SnackbarState['severity'] }>
        ) => {
            state.open = true;
            state.message = action.payload.message;
            state.severity = action.payload.severity;
        },
        hideSnackbar: (state) => {
            state.open = false;
        },
    },
});

export const { showSnackbar, hideSnackbar } = snackbarSlice.actions;
export default snackbarSlice.reducer;