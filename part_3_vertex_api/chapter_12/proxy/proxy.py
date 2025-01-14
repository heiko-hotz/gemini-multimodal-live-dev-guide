# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Vertex AI Gemini Multimodal Live WebSockets Proxy Server """
import asyncio
import json
import ssl
import traceback
import websockets
import certifi
import google.auth
import requests
from google.auth.transport.requests import Request
from urllib.parse import quote
from websockets.legacy.protocol import WebSocketCommonProtocol
from websockets.legacy.server import WebSocketServerProtocol


print("DEBUG: proxy.py - Starting script...")  # Add print here


HOST = "us-central1-aiplatform.googleapis.com"
SERVICE_URL = f"wss://{HOST}/ws/google.cloud.aiplatform.v1beta1.LlmBidiService/BidiGenerateContent"

DEBUG = True

# Track active connections
active_connections = set()

PROJECT_ID = "<YOUR_PROJECT_ID>"
LOCATION = "us-central1"

OPENWEATHER_API_KEY="<YOUR_OPENWEATHER_API_KEY>"

async def fetch_url(url: str) -> requests.Response:
    try:
        response = requests.get(url)

        # The request was successful (status code 200)
        if response.status_code == 200:
            return response.json()

        print('Error:', response.status_code)
        return None
    except requests.exceptions.RequestException as e:
        # Handle any network-related errors or exceptions
        print('Error:', e)
        return None


async def get_weather(city: str) -> dict:
    """
    Get the current weather for the given city name.

    Args:
        city: the name of the city to search the weather for.

    Returns:
        dict: weather results.
    """
    print("city: ", city)

    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={quote(city)}&limit=1&appid={OPENWEATHER_API_KEY}"
    geo_data = await fetch_url(geo_url)

    if not geo_data:
      print(f"Could not find location: {city}.")
      return None

    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    weather_data = await fetch_url(weather_url)
    if not weather_data:
      print(f"Could not find weather info for  {city}.")
      return None

    return {
      "temperature": weather_data["main"]["temp"],
      "description": weather_data["weather"][0]["description"],
      "humidity": weather_data["main"]["humidity"],
      "windSpeed": weather_data["wind"]["speed"],
      "city": weather_data["name"],
      "country": weather_data["sys"]["country"],
    }


def create_setup_message(system_instruction: str) -> dict:
    message = {}
    message["model"] = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-2.0-flash-exp"
    message["generation_config"] = {"response_modalities": ["audio"],
                                    "speech_config": {
                                        "voice_config": {
                                            "prebuilt_voice_config": {
                                                "voice_name": "Aoede"
                                            }
                                        }
                                    }}
    message["system_instruction"] = {"role": "user",
                                     "parts": [{"text": system_instruction}]}
    message["tools"] = [{"functionDeclarations": [{
                            "name": "get_weather",
                            "description": "Get current weather information for a city",
                            "parameters": {
                                "type": "OBJECT",
                                "properties": {
                                    "city": {
                                        "type": "STRING",
                                        "description": "The name of the city to get weather for"
                                    }
                                },
                                "required": ["city"]
                            }
                        }]}]
    return message


async def get_access_token():
    """Retrieves the access token for the currently authenticated account."""
    try:
        creds, _ = google.auth.default()  # Get the default credentials
        if not creds.valid:
            # Refresh the credentials if they're not valid
            request = Request()
            creds.refresh(request)
        return creds.token
    except Exception as e:
        print(f"Error getting access token: {e}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        raise


async def proxy_task(
    source_websocket: WebSocketCommonProtocol,
    target_websocket: WebSocketCommonProtocol,
    name: str = "",
) -> None:
    """
    Forwards messages from one WebSocket connection to another.
    """
    try:
        async for message in source_websocket:
            try:
                data = json.loads(message)

                # Log message type for debugging
                if "setup" in data:
                    print(f"{name} forwarding setup message")
                    print(f"Setup message content: {json.dumps(data, indent=2)}")
                elif "realtime_input" in data:
                    print(f"{name} forwarding audio/video input")
                elif "serverContent" in data:
                    has_audio = "inlineData" in str(data)
                    print(
                        f"{name} forwarding server content"
                        + (" with audio" if has_audio else "")
                    )
                elif "toolCall" in data:
                    print(f"Tool calling message: {json.dumps(data, indent=2)}")
                    function_responses = []
                    tool_call_response = {}
                    for function_call in data["toolCall"]["functionCalls"]:
                        if function_call["name"] == "get_weather":
                            weather_results = await get_weather(function_call["args"]["city"])
                            print(f"TOOL: get_weather output: {weather_results}")
                            function_responses.append({"name": function_call["name"],
                                                       "response": { "result" : { "object_value": weather_results}}})
                        tool_call_response = {"city": function_call["args"]["city"], "weather": weather_results}
                    await source_websocket.send(
                        json.dumps({"tool_response": { "function_responses": function_responses }}))

                    # Sends toolCallResponse purely for debugging purposes. No need to implement in the production system.
                    await target_websocket.send(json.dumps({"toolCallResponse": tool_call_response}))
                    # No need to forward the tool call message to clients.
                    continue
                else:
                    print(f"{name} forwarding message type: {list(data.keys())}")
                    print(f"Message content: {json.dumps(data, indent=2)}")

                # Forward the message
                try:
                    await target_websocket.send(json.dumps(data))
                except Exception as e:
                    print(f"\n{name} Error sending message:")
                    print("=" * 80)
                    print(f"Error details: {str(e)}")
                    print("=" * 80)
                    print(f"Message that failed: {json.dumps(data, indent=2)}")
                    raise

            except websockets.exceptions.ConnectionClosed as e:
                print(f"\n{name} connection closed during message processing:")
                print("=" * 80)
                print(f"Close code: {e.code}")
                print(f"Close reason (full):")
                print("-" * 40)
                print(e.reason)
                print("=" * 80)
                break
            except Exception as e:
                print(f"\n{name} Error processing message:")
                print("=" * 80)
                print(f"Error details: {str(e)}")
                print(f"Full traceback:\n{traceback.format_exc()}")
                print("=" * 80)

    except websockets.exceptions.ConnectionClosed as e:
        print(f"\n{name} connection closed:")
        print("=" * 80)
        print(f"Close code: {e.code}")
        print(f"Close reason (full):")
        print("-" * 40)
        print(e.reason)
        print("=" * 80)
    except Exception as e:
        print(f"\n{name} Error:")
        print("=" * 80)
        print(f"Error details: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print("=" * 80)
    finally:
        # Clean up connections when done
        print(f"{name} cleaning up connection")
        if target_websocket in active_connections:
            active_connections.remove(target_websocket)
        try:
            await target_websocket.close()
        except:
            pass


async def create_proxy(
    client_websocket: WebSocketCommonProtocol, bearer_token: str
) -> None:
    """
    Establishes a WebSocket connection to the server and creates two tasks for
    bidirectional message forwarding between the client and the server.
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
        }

        print(f"Connecting to {SERVICE_URL}")
        async with websockets.connect(
            SERVICE_URL,
            additional_headers=headers,
            ssl=ssl.create_default_context(cafile=certifi.where()),
        ) as server_websocket:
            print("Connected to Vertex AI")
            active_connections.add(server_websocket)

            try:
                f = open("system-instructions.txt", "r")
                system_instructions = f.read()
            except Exception as e:
                print(f"Error reading system-instructions.txt.")
                print(f"Error details: {str(e)}")
                print("=" * 80)

            setup_message = {"setup" : create_setup_message(system_instructions)}
            print(f"Sending setup message:\n {setup_message}")
            try:
                await server_websocket.send(json.dumps(setup_message))
            except Exception as e:
                print(f"\nError sending set up message:")
                print("=" * 80)
                print(f"Error details: {str(e)}")
                print("=" * 80)
                print(f"Message that failed: {json.dumps(setup_message, indent=2)}")
                raise

            # Create bidirectional proxy tasks
            client_to_server = asyncio.create_task(
                proxy_task(client_websocket, server_websocket, "Client->Server")
            )
            server_to_client = asyncio.create_task(
                proxy_task(server_websocket, client_websocket, "Server->Client")
            )

            try:
                # Wait for both tasks to complete
                await asyncio.gather(client_to_server, server_to_client)
            except Exception as e:
                print(f"Error during proxy operation: {e}")
                print(f"Full traceback: {traceback.format_exc()}")
            finally:
                # Clean up tasks
                for task in [client_to_server, server_to_client]:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

    except Exception as e:
        print(f"Error creating proxy connection: {e}")
        print(f"Full traceback: {traceback.format_exc()}")


async def handle_client(client_websocket: WebSocketServerProtocol) -> None:
    """
    Handles a new client connection.
    """
    print("New connection...")
    try:
        # Get auth token automatically
        bearer_token = await get_access_token()
        print("Retrieved bearer token automatically")

        # Send auth complete message to client
        await client_websocket.send(json.dumps({"authComplete": True}))
        print("Sent auth complete message")

        print("Creating proxy connection")
        await create_proxy(client_websocket, bearer_token)

    except asyncio.TimeoutError:
        print("Timeout in handle_client")
        await client_websocket.close(code=1008, reason="Auth timeout")
    except Exception as e:
        print(f"Error in handle_client: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        await client_websocket.close(code=1011, reason=str(e))


async def cleanup_connections() -> None:
    """
    Periodically clean up stale connections
    """
    while True:
        print(f"Active connections: {len(active_connections)}")
        for conn in list(active_connections):
            try:
                await conn.ping()
            except:
                print("Found stale connection, removing...")
                active_connections.remove(conn)
                try:
                    await conn.close()
                except:
                    pass
        await asyncio.sleep(30)  # Check every 30 seconds


async def main() -> None:
    """
    Starts the WebSocket server.
    """
    print(f"DEBUG: proxy.py - main() function started")
    # Get the port from the environment variable, defaulting to 8081
    # port = int(os.environ.get("PORT", 8081))
    port = 8081

    # Start the cleanup task
    cleanup_task = asyncio.create_task(cleanup_connections())

    async with websockets.serve(
        handle_client,
        "0.0.0.0",
        # "localhost",
        # 8080,
        port,
        ping_interval=30,  # Send ping every 30 seconds
        ping_timeout=10,  # Wait 10 seconds for pong
    ):
        print(f"Running websocket server on 0.0.0.0:{port}...")
        try:
            await asyncio.Future()  # run forever
        finally:
            cleanup_task.cancel()
            # Close all remaining connections
            for conn in list(active_connections):
                try:
                    await conn.close()
                except:
                    pass
            active_connections.clear()


if __name__ == "__main__":
    asyncio.run(main())
