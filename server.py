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
""" Pastra Tutorial Web Server"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
import traceback
from shared.tools.python.calendar_api import get_next_appointment
from shared.tools.python.weather_api import get_weather
from shared.tools.python.stock_api import get_stock_price

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def list_directory(self, path):
        # Enable directory listing
        return super().list_directory(path)

    def do_GET(self):
        try:
            if self.path.startswith('/calendar/next'):
                self.handle_api_request(get_next_appointment)
            elif self.path.startswith('/weather'):
                city = self.path.split('/')[-1]
                self.handle_api_request(lambda: get_weather(city))
            elif self.path.startswith('/stock'):
                symbol = self.path.split('/')[-1]
                self.handle_api_request(lambda: get_stock_price(symbol))
            else:
                super().do_GET()
        except Exception as e:
            self.send_error_response(e)

    def handle_api_request(self, handler_func):
        try:
            result = handler_func()
            self.send_json_response(result)
        except Exception as e:
            self.send_error_response(e)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_response(self, error):
        print(f"Error in request: {str(error)}")
        print("Full error details:")
        traceback.print_exc()
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_response = {
            'error': str(error),
            'type': type(error).__name__,
            'traceback': traceback.format_exc()
        }
        self.wfile.write(json.dumps(error_response).encode())

if __name__ == '__main__':
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    port = 8000
    print(f"Starting server at http://localhost:{port}")
    
    httpd = HTTPServer(('localhost', port), CORSRequestHandler)
    httpd.serve_forever() 