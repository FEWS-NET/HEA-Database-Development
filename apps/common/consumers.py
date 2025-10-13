import asyncio
import logging
import os

import websockets
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class DagsterWebSocketProxyConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        logger.info(f"WebSocket connection attempt: {self.scope['path']}")

        # Authentication check
        if isinstance(self.scope["user"], AnonymousUser):
            logger.error("Authentication required")
            raise DenyConnection("Authentication required")

        if not self.scope["user"].has_perm("common.access_dagster_ui"):
            logger.error(f"User {self.scope['user'].username} lacks permission")
            raise DenyConnection("Permission denied")

        logger.info(f"User {self.scope['user'].username} authenticated")

        # Build upstream URL
        dagster_url = os.environ.get("DAGSTER_WEBSERVER_URL", "http://localhost:3000")
        dagster_prefix = os.environ.get("DAGSTER_WEBSERVER_PREFIX", "")

        path = self.scope["path"]
        if path.startswith("/pipelines/"):
            path = path[len("/pipelines/") :]

        # Convert http to ws
        if dagster_url.startswith("https://"):
            ws_url = dagster_url.replace("https://", "wss://", 1)
        else:
            ws_url = dagster_url.replace("http://", "ws://", 1)

        # Build target URL
        if dagster_prefix:
            target_url = f"{ws_url}/{dagster_prefix}/{path}"
        else:
            target_url = f"{ws_url}/{path}"

        # Add query string
        if self.scope.get("query_string"):
            target_url += f"?{self.scope['query_string'].decode()}"

        logger.info(f"Connecting to upstream: {target_url}")

        # Get subprotocols from client
        subprotocols = self.scope.get("subprotocols", [])

        try:
            self.websocket = await websockets.connect(
                target_url,
                max_size=2097152,
                ping_interval=20,
                subprotocols=subprotocols if subprotocols else None,
            )
            logger.info("Connected to upstream")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise DenyConnection(f"Connection to upstream failed: {e}")

        await self.accept(self.websocket.subprotocol)
        logger.info(f"Client accepted with subprotocol: {self.websocket.subprotocol}")

        self.consumer_task = asyncio.create_task(self.consume_from_upstream())

    async def disconnect(self, close_code):
        logger.info(f"Disconnecting with code {close_code}")
        if hasattr(self, "consumer_task"):
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
        if hasattr(self, "websocket"):
            await self.websocket.close()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            await self.websocket.send(bytes_data or text_data)
        except Exception as e:
            logger.error(f"Error forwarding to upstream: {e}")
            await self.close()

    async def consume_from_upstream(self):
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error consuming from upstream: {e}")
            await self.close()
