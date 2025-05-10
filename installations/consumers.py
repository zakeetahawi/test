import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import WebsocketError
from .models import Installation, InstallationStep
from django.core.serializers.json import DjangoJSONEncoder
import asyncio
import logging

logger = logging.getLogger(__name__)

class InstallationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.installation_id = self.scope['url_route']['kwargs']['installation_id']
        self.room_group_name = f'installation_{self.installation_id}'
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1  # Start with 1 second delay

        try:
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Send initial state
            initial_state = await self.get_installation_state()
            await self.accept()
            await self.send(text_data=json.dumps({
                'type': 'initial_state',
                'data': initial_state
            }, cls=DjangoJSONEncoder))
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self.heartbeat())
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            await self.close()
            return

    async def heartbeat(self):
        while True:
            try:
                await self.send(text_data=json.dumps({'type': 'ping'}))
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
                await self.handle_connection_error()
                break

    async def handle_connection_error(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 30)  # Exponential backoff up to 30 seconds
            try:
                await self.connect()
                self.reconnect_attempts = 0  # Reset attempts on successful reconnection
                self.reconnect_delay = 1  # Reset delay
            except Exception as e:
                logger.error(f"Reconnection attempt {self.reconnect_attempts} failed: {str(e)}")
        else:
            logger.error("Max reconnection attempts reached")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'heartbeat_task'):
                self.heartbeat_task.cancel()
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'pong':
                return  # Handle heartbeat response
            elif message_type == 'status_update':
                await self.handle_status_update(text_data_json)
            elif message_type == 'step_update':
                await self.handle_step_update(text_data_json)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.handle_connection_error()

    async def installation_update(self, event):
        try:
            # Send message to WebSocket
            await self.send(text_data=json.dumps(event, cls=DjangoJSONEncoder))
        except Exception as e:
            logger.error(f"Error in installation_update: {str(e)}")
            await self.handle_connection_error()

    @database_sync_to_async
    def get_installation_state(self):
        try:
            installation = Installation.objects.select_related('team').get(id=self.installation_id)
            steps = InstallationStep.objects.filter(installation_id=self.installation_id).order_by('order')
            
            return {
                'installation': {
                    'id': installation.id,
                    'status': installation.status,
                    'scheduled_date': installation.scheduled_date,
                    'actual_start_date': installation.actual_start_date,
                    'actual_end_date': installation.actual_end_date,
                    'quality_rating': installation.quality_rating,
                    'notes': installation.notes
                },
                'team': {
                    'id': installation.team.id,
                    'name': installation.team.name,
                    'leader': {
                        'id': installation.team.leader.id,
                        'name': installation.team.leader.name
                    } if installation.team.leader else None
                },
                'steps': [{
                    'id': step.id,
                    'name': step.name,
                    'order': step.order,
                    'is_completed': step.is_completed,
                    'completed_at': step.completed_at
                } for step in steps],
                'completion_percentage': self.calculate_completion_percentage(steps)
            }
        except Installation.DoesNotExist:
            logger.error(f"Installation {self.installation_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting installation state: {str(e)}")
            raise

    @staticmethod
    def calculate_completion_percentage(steps):
        if not steps:
            return 0
        completed_steps = sum(1 for step in steps if step.is_completed)
        return (completed_steps / len(steps)) * 100

    async def handle_status_update(self, data):
        try:
            await self._update_installation_status(data['status'])
            
            # Broadcast status update to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'installation_update',
                    'message_type': 'status_update',
                    'status': data['status']
                }
            )
        except Exception as e:
            logger.error(f"Error in handle_status_update: {str(e)}")
            await self.handle_connection_error()

    async def handle_step_update(self, data):
        try:
            completion_percentage = await self._update_step_status(data)
            
            # Broadcast step update to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'installation_update',
                    'message_type': 'step_update',
                    'step_id': data['step_id'],
                    'is_completed': data['is_completed'],
                    'completion_percentage': completion_percentage
                }
            )
        except Exception as e:
            logger.error(f"Error in handle_step_update: {str(e)}")
            await self.handle_connection_error()

    @database_sync_to_async
    def _update_installation_status(self, status):
        try:
            installation = Installation.objects.get(id=self.installation_id)
            installation.status = status
            installation.save()
        except Exception as e:
            logger.error(f"Error updating installation status: {str(e)}")
            raise

    @database_sync_to_async
    def _update_step_status(self, data):
        try:
            step = InstallationStep.objects.get(id=data['step_id'])
            step.is_completed = data['is_completed']
            step.save()

            steps = InstallationStep.objects.filter(installation_id=self.installation_id)
            return self.calculate_completion_percentage(steps)
        except Exception as e:
            logger.error(f"Error updating step status: {str(e)}")
            raise
