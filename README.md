# 🧠 mcp-core

`mcp-core` is the central monorepo for backend services and core logic powering a modular MCP (Machine Command Protocol) ecosystem.

## 📌 Purpose

This monorepo serves as the foundation for building intelligent, language-driven backend services. Each server in `mcp-core` is responsible for interpreting natural language commands and executing relevant tasks (e.g., interacting with Docker, Git, or other dev tools).

### Why a monorepo?

- ✅ **Unified structure**: Easier to maintain shared logic across multiple MCP servers  
- 🔄 **Reusability**: Common interfaces, utils, and core services live in one place  
- 📚 **Consistency**: Code style, testing, and CI/CD pipelines are standardized  
- 🧩 **Modular growth**: New MCP servers can be added without fragmenting the ecosystem

### Key Goals

- Use IA as infrastructure interface.
- Provide a scalable backend architecture for natural language-driven automation
- Enable seamless integration with tools like Visual Studio Code, Docker, Git, etc.
- Encourage modular development and clean separation of responsibilities

## 📁 Structure (example)

