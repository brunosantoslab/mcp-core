import json
import docker
from http.server import BaseHTTPRequestHandler, HTTPServer

# Start-up message
print("Starting MCP server...")

# Attempt to connect to Docker
try:
    print("Attempting Docker connection...")
    client = docker.from_env()  # Connects to the local Docker daemon
    print("Docker connection successful!")
except Exception as e:
    print(f"Error connecting to Docker: {e}")
    exit(1)

# Define the HTTP request handler
class MCPDockerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read the incoming POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request = json.loads(post_data)
        command = request.get('command')
        print(f"Received command: {command}")

        # Handle different Docker commands
        if command == 'list_containers':
            containers = [c.name for c in client.containers.list()]
            response = {'result': containers}
            status = 200
        elif command == 'get_container_status':
            container_id = request.get('container_id')
            if container_id:
                try:
                    container = client.containers.get(container_id)
                    response = {'result': {'status': container.status, 'image': container.image.tags}}
                    status = 200
                except docker.errors.NotFound:
                    response = {'error': 'Container not found'}
                    status = 404
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Container ID not provided'}
                status = 400
        elif command == 'start_container':
            container_id = request.get('container_id')
            if container_id:
                try:
                    container = client.containers.get(container_id)
                    container.start()
                    response = {'result': f'Container {container_id} started'}
                    status = 200
                except docker.errors.NotFound:
                    response = {'error': 'Container not found'}
                    status = 404
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Container ID not provided'}
                status = 400
        elif command == 'stop_container':
            container_id = request.get('container_id')
            if container_id:
                try:
                    container = client.containers.get(container_id)
                    container.stop()
                    response = {'result': f'Container {container_id} stopped'}
                    status = 200
                except docker.errors.NotFound:
                    response = {'error': 'Container not found'}
                    status = 404
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Container ID not provided'}
                status = 400
        elif command == 'remove_container':
            container_id = request.get('container_id')
            if container_id:
                try:
                    container = client.containers.get(container_id)
                    container.remove()
                    response = {'result': f'Container {container_id} removed'}
                    status = 200
                except docker.errors.NotFound:
                    response = {'error': 'Container not found'}
                    status = 404
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Container ID not provided'}
                status = 400
        elif command == 'list_images':
            images = [img.tags[0] if img.tags else img.id for img in client.images.list()]
            response = {'result': images}
            status = 200
        elif command == 'pull_image':
            image_name = request.get('image_name')
            if image_name:
                try:
                    client.images.pull(image_name)
                    response = {'result': f'Image {image_name} pulled successfully'}
                    status = 200
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Image name not provided'}
                status = 400
        elif command == 'run_container':
            image_name = request.get('image_name')
            container_name = request.get('container_name', None)
            if image_name:
                try:
                    container = client.containers.run(image_name, name=container_name, detach=True)
                    response = {'result': f'Container {container.name} started from image {image_name}'}
                    status = 200
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Image name not provided'}
                status = 400
        elif command == 'get_container_logs':
            container_id = request.get('container_id')
            if container_id:
                try:
                    container = client.containers.get(container_id)
                    logs = container.logs().decode('utf-8')
                    response = {'result': logs}
                    status = 200
                except docker.errors.NotFound:
                    response = {'error': 'Container not found'}
                    status = 404
                except Exception as e:
                    response = {'error': str(e)}
                    status = 500
            else:
                response = {'error': 'Container ID not provided'}
                status = 400
        else:
            response = {'error': 'Unknown command'}
            status = 400

        # Send the response back to the client
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

# Function to run the server
def run_server():
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, MCPDockerHandler)
    print("🚀 MCP server running at http://localhost:8000")
    httpd.serve_forever()

# Start the server if this file is run directly
if __name__ == '__main__':
    run_server()