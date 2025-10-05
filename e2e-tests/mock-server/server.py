#!/usr/bin/env python3
"""
Mock EdgeIQ API Server with embedded MQTT broker
Provides HTTP endpoints for config downloads and MQTT broker for device communication
"""

import asyncio
import json
import logging
import os
import re
import zipfile
from io import BytesIO
from pathlib import Path

import paho.mqtt.client as mqtt
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockMQTTBroker:
    """Simple MQTT broker that accepts all connections and publishes to # topic"""

    def __init__(self, host='0.0.0.0', port=1883):
        self.host = host
        self.port = port
        self.broker = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.broker.on_connect = self.on_connect
        self.broker.on_message = self.on_message
        self.broker.on_subscribe = self.on_subscribe

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Handle client connection"""
        logger.info(f"MQTT Client connected with result code: {reason_code}")
        # Subscribe to all topics
        client.subscribe("#")

    def on_message(self, client, userdata, msg):
        """Handle incoming messages and republish to # topic"""
        logger.info(f"MQTT Message received on topic '{msg.topic}': {msg.payload.decode()}")
        # Republish to # topic
        client.publish("#", msg.payload)

    def on_subscribe(self, client, userdata, mid, reason_codes, properties):
        """Handle subscription events"""
        logger.info(f"MQTT Subscription successful: {reason_codes}")

    async def start(self):
        """Start the MQTT broker"""
        logger.info(f"Starting MQTT broker on {self.host}:{self.port}")
        self.broker.connect(self.host, self.port, 60)

        # Run broker loop in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.broker.loop_forever)


class MockHTTPServer:
    """HTTP server that mocks EdgeIQ API endpoints"""

    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_get('/api/v1/platform/configs_v3/{carrier}/{filename}', self.handle_config_download)
        self.app.router.add_get('/health', self.handle_health)

    async def handle_health(self, request):
        """Health check endpoint"""
        return web.json_response({'status': 'ok'})

    async def handle_config_download(self, request):
        """
        Handle config download requests matching pattern:
        /api/v1/platform/configs_v3/{carrier}/{filename}.zip

        Returns a zip file containing config.json
        """
        carrier = request.match_info['carrier']
        filename = request.match_info['filename']

        logger.info(f"Received config download request: carrier={carrier}, filename={filename}")

        # Load mock config response
        # Use environment variable or default to ../fixtures/responses
        responses_dir = Path(os.getenv('RESPONSES_DIR', '/home/ubuntu/fixtures/responses'))
        config_file = responses_dir / 'config.json'

        if not config_file.exists():
            # Create default config if it doesn't exist
            default_config = {
                "version": "1.0.0",
                "edge": {
                    "relay_frequency_limit": 10,
                    "log_level": "info"
                },
                "device": {
                    "carrier": carrier,
                    "unique_id": carrier
                }
            }
            config_content = json.dumps(default_config, indent=2).encode('utf-8')
        else:
            config_content = config_file.read_bytes()

        # Create zip file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('config.json', config_content)

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()

        logger.info(f"Returning config zip file: {len(zip_data)} bytes")

        return web.Response(
            body=zip_data,
            content_type='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}.zip"'
            }
        )

    async def start(self):
        """Start the HTTP server"""
        logger.info(f"Starting HTTP server on {self.host}:{self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()


async def main():
    """Run both HTTP and MQTT servers"""
    # Create responses directory if it doesn't exist
    responses_dir = Path(os.getenv('RESPONSES_DIR', '/home/ubuntu/fixtures/responses'))
    responses_dir.mkdir(parents=True, exist_ok=True)

    # Start HTTP server
    http_server = MockHTTPServer()
    await http_server.start()
    logger.info("HTTP server started successfully")

    # Note: MQTT broker requires external broker like Mosquitto
    # For simplicity, we'll just run HTTP server
    # MQTT broker runs separately on the host (see Makefile services-start)

    logger.info("Mock server ready to accept connections")
    logger.info("HTTP: http://0.0.0.0:8080")
    logger.info("MQTT: mqtt://0.0.0.0:1883")

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down mock server")


if __name__ == '__main__':
    asyncio.run(main())
