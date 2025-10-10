#!/usr/bin/env python3
"""
Mock EdgeIQ API Server with embedded MQTT broker
Provides HTTP endpoints for config downloads and MQTT broker for device communication
"""

import asyncio
import hashlib
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
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to: {log_level}")


def generate_app_config_zip(company_id, device_unique_id):
    """
    Generate app_config.zip file content and return (zip_data, json_md5_hash, zip_md5_hash)

    Args:
        company_id: Company ID for the config
        device_unique_id: Device unique ID for the config

    Returns:
        Tuple of (zip_data: bytes, json_md5_hash: str, zip_md5_hash: str)
        - json_md5_hash: MD5 hash of the JSON file content (used in MQTT response)
        - zip_md5_hash: MD5 hash of the zip file content (for reference)
    """
    logger.debug(f"Generating app_config.zip for company_id={company_id}, device_unique_id={device_unique_id}")

    # Load mock app_config response
    responses_dir = Path(os.getenv('RESPONSES_DIR', '/home/ubuntu/fixtures/responses'))
    app_config_file = responses_dir / 'app_config.json'

    logger.debug(f"Looking for app_config.json at: {app_config_file}")

    if not app_config_file.exists():
        logger.debug("app_config.json not found, generating default config")
        # Create default app_config if it doesn't exist
        default_app_config = {
            "id": "642b74cc7ac462445dba7457",
            "name": device_unique_id,
            "unique_id": device_unique_id,
            "auto_relay_reports": False,
            "aws_greengrass_core_thing_arn": "",
            "bluemix_auth_token": "",
            "heartbeat_period": 5,
            "heartbeat_values": None,
            "max_persisted_reports": 1000,
            "relay_frequency_limit_seconds": 0,
            "metadata": {},
            "company": {
                "id": company_id,
                "company_id": company_id,
                "name": "edge testing company",
                "user_id": "5bb3e6d773c6b700018695fa",
                "created_at": "2023-04-04T00:52:27.154015Z",
                "updated_at": "2023-04-04T00:52:27.154015Z",
                "origin": "cloud",
                "aliases": {
                    "device": "device",
                    "gateway": "gateway"
                },
                "branding": {
                    "gradient_sidbar": False,
                    "icon_url": "",
                    "logo_background_color": "",
                    "logo_url": "",
                    "portal_title": "",
                    "primary_color": "",
                    "secondary_color": "",
                    "sidebar_text_color": ""
                }
            },
            "device_type": {
                "id": "642b74cc7ac462445dba7455",
                "name": "Remote Terminal Test Device Type",
                "type": "gateway",
                "role": "gateway",
                "manufacturer": "ManFac",
                "model": "3 Million",
                "company_id": company_id,
                "user_id": "642b74cb7ac462445dba7453",
                "origin": "cloud",
                "created_at": "2023-04-04T00:52:28.001016Z",
                "updated_at": "2023-04-04T00:52:28.001016Z",
                "capabilities": {
                    "actions": {
                        "heartbeat": True,
                        "log": True,
                        "log_config": True,
                        "log_level": True,
                        "log_upload": True,
                        "mqtt": True,
                        "send_config": True,
                        "setting": True,
                        "start_remote_terminal": True,
                        "status": True,
                        "stop_remote_terminal": True
                    }
                },
                "rules": [],
                "command_ids": [],
                "ingestor_ids": [],
                "software_update_ids": [],
                "pollable_attributes": []
            },
            "user": {
                "id": "642b74cb7ac462445dba7453",
                "company_id": company_id,
                "user_id": "5bb3e6d773c6b700018695fa",
                "email": "edge-testing@edgeiq.io",
                "first_name": "EdgeIQ",
                "last_name": "Tester",
                "phone_number": "",
                "encrypted_authentication_token": "wFkiS.$2a$10$...",
                "encrypted_password": "$2a$10$...",
                "logo_url": "",
                "origin": "cloud",
                "created_at": "2023-04-04T00:52:27.640092Z",
                "updated_at": "2023-04-04T00:52:27.640092Z"
            },
            "log_config": {
                "local_level": "info",
                "forward_level": "error",
                "forward_frequency_limit": 60
            },
            "device_types": [],
            "devices": [],
            "connections": [],
            "ingestors": [],
            "translators": [],
            "commands": [],
            "integrations": [],
            "integration_ids": [],
            "rules": [],
            "device_ha_group": None
        }
        app_config_content = json.dumps(default_app_config, indent=2).encode('utf-8')
        logger.debug(f"Generated default config: {len(app_config_content)} bytes")
    else:
        app_config_content = app_config_file.read_bytes()
        logger.debug(f"Loaded app_config.json from file: {len(app_config_content)} bytes")

    # Compute MD5 hash of JSON file content (this is what MQTT response should use)
    json_md5_hash = hashlib.md5(app_config_content).hexdigest()
    logger.debug(f"JSON content MD5 hash: {json_md5_hash}")

    # Create zip file in memory with app_config.json at root level
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('app_config.json', app_config_content)

    logger.debug("Created zip archive with app_config.json")

    zip_buffer.seek(0)
    zip_data = zip_buffer.read()

    # Compute MD5 hash of zip file content (for reference/debugging)
    zip_md5_hash = hashlib.md5(zip_data).hexdigest()

    logger.debug(f"Generated zip: {len(zip_data)} bytes, zip MD5: {zip_md5_hash}, json MD5: {json_md5_hash}")

    return zip_data, json_md5_hash, zip_md5_hash


class MockMQTTServer:
    """MQTT client that connects to Mosquitto broker and responds to device config requests"""

    def __init__(self, host='localhost', port=1883, max_retries=30, retry_delay=2):
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="edgeiq-mock-server")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Handle connection to Mosquitto broker"""
        logger.debug(f"on_connect called: reason_code={reason_code}, flags={flags}")
        if reason_code == 0:
            logger.info(f"MQTT Client successfully connected to Mosquitto broker at {self.host}:{self.port}")
            self.connected = True
            # Subscribe to uplink config topic pattern: u/+/+/config
            result = client.subscribe("u/+/+/config")
            logger.debug(f"Subscribe result: {result}")
            logger.info("Subscribed to topic pattern: u/+/+/config")
        else:
            logger.error(f"MQTT Client connection failed with result code: {reason_code}")
            self.connected = False

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Handle disconnection from broker"""
        logger.warning(f"MQTT Client disconnected with result code: {reason_code}")
        self.connected = False

    def on_message(self, client, userdata, msg):
        """Handle incoming messages and respond with appropriate commands"""
        topic = msg.topic
        payload = msg.payload.decode()
        logger.info(f"MQTT Message received on topic '{topic}': {payload}")

        # Parse config request: u/<company_id>/<device_unique_id>/config
        if topic.startswith('u/') and topic.endswith('/config'):
            logger.debug(f"Detected config request topic: {topic}")
            try:
                payload_data = json.loads(payload)
                logger.debug(f"Parsed payload: {payload_data}")

                # Check if this is a config v3 request
                if payload_data.get('config_version') == 3 and payload_data.get('requested'):
                    logger.debug("Detected config v3 request with 'requested' flag")
                    # Extract company_id and device_unique_id from topic
                    topic_parts = topic.split('/')
                    logger.debug(f"Topic parts: {topic_parts}")
                    if len(topic_parts) >= 3:
                        company_id = topic_parts[1]
                        device_unique_id = topic_parts[2]
                        logger.debug(f"Extracted IDs - company_id: {company_id}, device_unique_id: {device_unique_id}")

                        # Build response topic: d/<company_id>/<device_unique_id>/gateway_commands/send_config_v3
                        response_topic = f"d/{company_id}/{device_unique_id}/gateway_commands/send_config_v3"
                        logger.debug(f"Response topic: {response_topic}")

                        # Get mock server host from environment or use default
                        mock_server_host = os.getenv('MOCK_SERVER_HOST', 'localhost')
                        mock_server_port = os.getenv('MOCK_SERVER_PORT', '8080')
                        logger.debug(f"Mock server endpoint: {mock_server_host}:{mock_server_port}")

                        # Build config download URL
                        config_url = f"http://{mock_server_host}:{mock_server_port}/api/v1/platform/configs_v3/{company_id}/{device_unique_id}/app_config.zip"
                        logger.debug(f"Config URL: {config_url}")

                        # Generate zip and get MD5 hash of JSON content (not zip)
                        _, json_md5_hash, zip_md5_hash = generate_app_config_zip(company_id, device_unique_id)
                        logger.debug(f"Using JSON MD5 hash for MQTT response: {json_md5_hash}")
                        logger.debug(f"Zip MD5 hash (for reference): {zip_md5_hash}")

                        # Build response payload with JSON MD5 hash
                        response = {
                            "command_type": "send_config_v3",
                            "payload": {
                                "url": config_url,
                                "md5": json_md5_hash
                            }
                        }

                        response_json = json.dumps(response)
                        logger.info(f"Publishing config response to topic '{response_topic}': {response_json}")
                        publish_result = client.publish(response_topic, response_json, qos=1)
                        logger.debug(f"Publish result: {publish_result}")
                    else:
                        logger.warning(f"Invalid topic format (expected at least 3 parts): {topic}")
                else:
                    logger.debug(f"Not a config v3 request: config_version={payload_data.get('config_version')}, requested={payload_data.get('requested')}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse MQTT message payload: {e}")
        else:
            logger.debug(f"Ignoring non-config topic: {topic}")

    async def wait_for_broker(self):
        """Wait for Mosquitto broker to be available"""
        logger.info(f"Waiting for Mosquitto broker at {self.host}:{self.port}...")
        logger.debug(f"Max retries: {self.max_retries}, retry delay: {self.retry_delay}s")

        for attempt in range(1, self.max_retries + 1):
            try:
                # Try to connect
                logger.info(f"Connection attempt {attempt}/{self.max_retries}")
                logger.debug(f"Calling client.connect({self.host}, {self.port}, 60)")
                self.client.connect(self.host, self.port, 60)

                # Start network loop in background
                logger.debug("Starting MQTT network loop")
                self.client.loop_start()

                # Wait a bit for connection callback
                logger.debug("Waiting 1 second for connection callback")
                await asyncio.sleep(1)

                if self.connected:
                    logger.info("Successfully connected to Mosquitto broker")
                    return True
                else:
                    logger.debug("Connection callback not received yet")

            except Exception as e:
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                logger.debug(f"Exception type: {type(e).__name__}, details: {str(e)}")

            if attempt < self.max_retries:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                await asyncio.sleep(self.retry_delay)

        logger.error(f"Failed to connect to Mosquitto broker after {self.max_retries} attempts")
        return False

    async def start(self):
        """Start the MQTT client and connect to broker"""
        success = await self.wait_for_broker()
        if not success:
            raise ConnectionError(f"Could not connect to Mosquitto broker at {self.host}:{self.port}")
        
        logger.info("MQTT client running and subscribed to config requests")

    def stop(self):
        """Stop the MQTT client"""
        logger.info("Stopping MQTT client...")
        self.client.loop_stop()
        self.client.disconnect()


class MockHTTPServer:
    """HTTP server that mocks EdgeIQ API endpoints"""

    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_get('/api/v1/platform/configs_v3/{company_id}/{device_unique_id}/app_config.zip', self.handle_config_download)
        self.app.router.add_get('/health', self.handle_health)

    async def handle_health(self, request):
        """Health check endpoint"""
        return web.json_response({'status': 'ok'})

    async def handle_config_download(self, request):
        """
        Handle config download requests matching pattern:
        GET /api/v1/platform/configs_v3/{company_id}/{device_unique_id}/app_config.zip?token={auth_token}

        Returns a zip file containing app_config.json at root level
        """
        company_id = request.match_info['company_id']
        device_unique_id = request.match_info['device_unique_id']
        auth_token = request.query.get('token', '')

        logger.info(f"HTTP GET /api/v1/platform/configs_v3/{company_id}/{device_unique_id}/app_config.zip")
        logger.debug(f"Request details - company_id: {company_id}, device_unique_id: {device_unique_id}")
        logger.debug(f"Auth token (first 20 chars): {auth_token[:20] if auth_token else 'NONE'}...")
        logger.debug(f"Request headers: {dict(request.headers)}")

        # Generate zip file and MD5 hashes
        zip_data, json_md5_hash, zip_md5_hash = generate_app_config_zip(company_id, device_unique_id)

        logger.info(f"Returning app_config.zip file: {len(zip_data)} bytes")
        logger.debug(f"JSON MD5: {json_md5_hash}, Zip MD5: {zip_md5_hash}")

        response_headers = {
            'Content-Disposition': 'attachment; filename="app_config.zip"',
            'Content-Length': str(len(zip_data))
        }
        logger.debug(f"Response headers: {response_headers}")

        return web.Response(
            body=zip_data,
            content_type='application/zip',
            headers=response_headers
        )

    async def start(self):
        """Start the HTTP server"""
        logger.info(f"Starting HTTP server on {self.host}:{self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()


async def main():
    """Run both HTTP server and MQTT client"""
    logger.info("=" * 60)
    logger.info("EdgeIQ Mock Server Starting")
    logger.info("=" * 60)

    # Create responses directory if it doesn't exist
    responses_dir = Path(os.getenv('RESPONSES_DIR', '/home/ubuntu/fixtures/responses'))
    logger.debug(f"Responses directory: {responses_dir}")
    responses_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Responses directory exists: {responses_dir.exists()}")

    # Get configuration from environment
    mqtt_host = os.getenv('MQTT_HOST', 'localhost')
    mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
    http_host = os.getenv('HTTP_HOST', '0.0.0.0')
    http_port = int(os.getenv('HTTP_PORT', '8080'))

    logger.info("Configuration:")
    logger.info(f"  MQTT: {mqtt_host}:{mqtt_port}")
    logger.info(f"  HTTP: {http_host}:{http_port}")
    logger.info(f"  Responses: {responses_dir}")

    # Start MQTT client first (waits for Mosquitto to be available)
    logger.info("Initializing MQTT client...")
    mqtt_client = MockMQTTServer(host=mqtt_host, port=mqtt_port)
    try:
        logger.debug("Starting MQTT client connection process")
        await mqtt_client.start()
        logger.info("✓ MQTT client started successfully")
    except ConnectionError as e:
        logger.error(f"✗ Failed to start MQTT client: {e}")
        logger.warning("Continuing without MQTT client...")

    # Start HTTP server
    logger.info("Initializing HTTP server...")
    http_server = MockHTTPServer(host=http_host, port=http_port)
    logger.debug("Starting HTTP server")
    await http_server.start()
    logger.info("✓ HTTP server started successfully")

    logger.info("=" * 60)
    logger.info("Mock server ready to accept connections")
    logger.info(f"  Health check: http://{http_host}:{http_port}/health")
    logger.info(f"  Config API: http://{http_host}:{http_port}/api/v1/platform/configs_v3/{{company_id}}/{{device_id}}/app_config.zip")
    logger.info(f"  MQTT broker: mqtt://{mqtt_host}:{mqtt_port}")
    logger.info(f"  MQTT subscribed to: u/+/+/config")
    logger.info("=" * 60)

    # Keep running
    try:
        logger.debug("Entering main event loop")
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down mock server")
        logger.debug("Stopping MQTT client")
        mqtt_client.stop()
        logger.info("Mock server stopped")


if __name__ == '__main__':
    asyncio.run(main())
