# Build an MCP Server to Control Docker with GitHub Copilot Agent

This project showcases a **Model Context Protocol (MCP)** server built in Python to control Docker containers using natural language commands via the **GitHub Copilot Agent**. Designed for Windows environments, it bridges AI and your Docker infrastructure, enabling intuitive automation and management.

---

## Why This Project?

Imagine managing Docker with commands like "list active containers" or "stop all nginx containers" without tedious scripting. This MCP server makes it possible by:
- **Infinite Customization**: Tailor commands to your exact needs (e.g., "restart my web app containers").
- **Scalability**: Extend to manage multiple tools or complex workflows.
- **Time-Saving**: Why waste time when AI already understands your containers? Use natural language to get things done fast.
- **Direct Docker API Access**: Reliable, structured JSON responses for seamless integration.

---

## Features

The server supports key Docker operations, accessible via simple JSON requests:
- **List Containers**: See all running containers.
- **Start/Stop Containers**: Control container states.
- **Remove Containers**: Clean up with ease.
- **Pull Images**: Fetch images from registries.
- **Run Containers**: Launch new containers.
- **View Logs**: Inspect container logs.

---

## Prerequisites

- **Python 3.8+**
- **Docker Desktop** installed and running on Windows
- **VS Code** with the **GitHub Copilot** extension

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/mcp-docker-server.git
   cd mcp-docker-server```
   
2. **Install Dependencies**:
   ```bash
   pip install docker```
   
3. **Start the Server**:
   ```bash
   python mcp_docker_server.py```
   
The server runs on http://localhost:8000.

---

## Usage
**Send commands via HTTP POST requests. Example with curl**:
   ```bash curl -X POST http://localhost:8000 -H "Content-Type: application/json" -d '{"command": "list_containers"}'```

**Response**: 
   ```json {"result": ["container1", "container2"]}```
   
---   
   
## Supported Commands

- **list_containers** List all running containers
- **start_container** Start a stopped container
- **stop_container** Stop a running container
- **remove_container** Delete a container
- **list_images** List all Docker images
- **pull_image** Pull an image from a registry
- **run_container**	Run a new container from an image
- **get_container_logs** Fetch logs of a container

---

## Integrate with GitHub Copilot Agent
1. **Open VS Code and activate GitHub Copilot.**
2. **Register the MCP Server:**
3. **Open Chat (Ctrl+Alt+I).**
4. **Go to "Tools" > "Add":
5. **Name: DockerMCP
6. **Type: HTTP
7. **URL: http://localhost:8000
5. **Use Natural Language:** In Chat, select "Agent" and type: "Use DockerMCP to list active containers."

---

## Contribution
Love the idea? Contributions are welcome! Open issues or submit pull requests to enhance functionality.
    
