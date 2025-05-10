import React from 'react';
import useWebSocket from 'react-use-websocket';
import { useSnackbar } from 'notistack';
import { InstallationUpdate } from '../types/installation';

interface Props {
  installationId: string;
  onUpdate: (update: InstallationUpdate) => void;
}

export const InstallationConsumer: React.FC<Props> = ({ installationId, onUpdate }) => {
  const { enqueueSnackbar } = useSnackbar();
  const socketUrl = `ws://${window.location.host}/ws/installations/${installationId}/`;

  const { lastJsonMessage } = useWebSocket(socketUrl, {
    onOpen: () => {
      enqueueSnackbar('تم الاتصال بنظام التتبع المباشر', { 
        variant: 'success',
        anchorOrigin: { vertical: 'top', horizontal: 'center' },
      });
    },
    onError: () => {
      enqueueSnackbar('حدث خطأ في الاتصال بنظام التتبع', {
        variant: 'error',
        anchorOrigin: { vertical: 'top', horizontal: 'center' },
      });
    },
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data) as InstallationUpdate;
        onUpdate(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    },
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });

  React.useEffect(() => {
    if (lastJsonMessage) {
      onUpdate(lastJsonMessage as InstallationUpdate);
    }
  }, [lastJsonMessage, onUpdate]);

  return null;
};