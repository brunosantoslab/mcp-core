# MCP WhatsApp API Documentation

This document describes the API endpoints provided by the MCP WhatsApp Server and the WebSocket API provided by the WhatsApp Gateway.

## MCP WhatsApp Server API

The MCP WhatsApp Server provides a RESTful API for interacting with WhatsApp.

Base URL: `http://localhost:8080/api`

### Authentication

#### Get QR Code

```
GET /auth/qrcode
```

Returns the QR code for WhatsApp authentication or the authentication status.

**Response:**

```json
{
  "success": true,
  "qrCode": "BASE64_ENCODED_QR_CODE"
}
```

or if already authenticated:

```json
{
  "success": true,
  "authenticated": true
}
```

### Contacts

#### Get Contacts

```
GET /contacts
```

Returns a list of WhatsApp contacts.

**Response:**

```json
{
  "success": true,
  "contacts": [
    {
      "id": "contact_id",
      "name": "Contact Name",
      "number": "1234567890",
      "isGroup": false,
      "isMyContact": true
    },
    {
      "id": "group_id",
      "name": "Group Name",
      "number": "",
      "isGroup": true,
      "isMyContact": false
    }
  ]
}
```

### Chats

#### Get Chats

```
GET /chats
```

Returns a list of WhatsApp chats.

**Response:**

```json
{
  "success": true,
  "chats": [
    {
      "id": "chat_id",
      "name": "Chat Name",
      "isGroup": false,
      "timestamp": "2023-01-01T00:00:00Z",
      "unreadCount": 0
    }
  ]
}
```

#### Get Chat Messages

```
GET /chats/{chat_id}/messages?limit={limit}
```

Returns messages from a specific chat.

**Parameters:**

- `chat_id`: ID of the chat
- `limit` (optional): Maximum number of messages to return (default: 50)

**Response:**

```json
{
  "success": true,
  "messages": [
    {
      "id": "message_id",
      "chatId": "chat_id",
      "content": "Hello, world!",
      "timestamp": "2023-01-01T00:00:00Z",
      "sender": {
        "id": "sender_id",
        "name": "Sender Name"
      },
      "hasMedia": false,
      "isGroup": false,
      "isForwarded": false,
      "mentionedIds": []
    }
  ]
}
```

### Messages

#### Send Message

```
POST /messages
```

Sends a text message to a chat.

**Request Body:**

```json
{
  "chat_id": "chat_id",
  "content": "Hello, world!"
}
```

**Response:**

```json
{
  "success": true,
  "message": {
    "id": "message_id",
    "chatId": "chat_id",
    "content": "Hello, world!",
    "timestamp": "2023-01-01T00:00:00Z",
    "sender": {
      "id": "sender_id",
      "name": "Sender Name"
    },
    "hasMedia": false,
    "isGroup": false,
    "isForwarded": false,
    "mentionedIds": []
  }
}
```

#### Send Media

```
POST /media
```

Sends a media message to a chat.

**Request Body:**

```json
{
  "chat_id": "chat_id",
  "media": "BASE64_ENCODED_MEDIA",
  "filename": "example.jpg",
  "caption": "Check this out!",
  "media_type": "image"
}
```

**Response:**

```json
{
  "success": true,
  "message": {
    "id": "message_id",
    "chatId": "chat_id",
    "content": "Check this out!",
    "timestamp": "2023-01-01T00:00:00Z",
    "sender": {
      "id": "sender_id",
      "name": "Sender Name"
    },
    "hasMedia": true,
    "isGroup": false,
    "isForwarded": false,
    "mentionedIds": []
  }
}
```

#### Upload Media

```
POST /media/upload
```

Uploads media and sends it to a chat. This endpoint accepts `multipart/form-data`.

**Form Parameters:**

- `chat_id`: ID of the chat
- `file`: Media file to upload
- `caption` (optional): Caption for the media

**Response:**

Same as the Send Media endpoint.

### Search

#### Search Messages

```
POST /search
```

Searches for messages containing specific text.

**Request Body:**

```json
{
  "query": "search term",
  "chat_id": "chat_id"  // Optional, if not provided, searches all chats
}
```

**Response:**

```json
{
  "success": true,
  "messages": [
    {
      "id": "message_id",
      "chatId": "chat_id",
      "content": "This is a message containing the search term",
      "timestamp": "2023-01-01T00:00:00Z",
      "sender": {
        "id": "sender_id",
        "name": "Sender Name"
      },
      "hasMedia": false,
      "isGroup": false,
      "isForwarded": false,
      "mentionedIds": []
    }
  ]
}
```

## WhatsApp Gateway WebSocket API

The WhatsApp Gateway provides a WebSocket API for real-time communication.

WebSocket URL: `ws://localhost:8090/ws`

### Message Types

The WebSocket API uses the following message types:

- `command`: Commands sent from the client to the gateway
- `response`: Responses to commands
- `event`: Events from WhatsApp
- `error`: Error messages

### Commands

Commands are sent as JSON objects with the following structure:

```json
{
  "type": "command",
  "id": "unique_request_id",
  "command": "command_name",
  "data": {
    // Command-specific data
  }
}
```

#### Get Contacts

```json
{
  "type": "command",
  "id": "request_id",
  "command": "getContacts"
}
```

#### Get Chats

```json
{
  "type": "command",
  "id": "request_id",
  "command": "getChats"
}
```

#### Get Chat Messages

```json
{
  "type": "command",
  "id": "request_id",
  "command": "getChatMessages",
  "data": {
    "chatId": "chat_id",
    "limit": 50
  }
}
```

#### Send Message

```json
{
  "type": "command",
  "id": "request_id",
  "command": "sendMessage",
  "data": {
    "chatId": "chat_id",
    "content": "Hello, world!"
  }
}
```

#### Send Media

```json
{
  "type": "command",
  "id": "request_id",
  "command": "sendMedia",
  "data": {
    "chatId": "chat_id",
    "media": "BASE64_ENCODED_MEDIA",
    "filename": "example.jpg",
    "caption": "Check this out!",
    "mediaType": "image"
  }
}
```

### Responses

Responses are sent as JSON objects with the following structure:

```json
{
  "type": "response",
  "id": "request_id",
  "command": "command_name",
  "data": {
    // Command-specific response data
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Events

Events are sent as JSON objects with the following structure:

```json
{
  "type": "event",
  "event": "event_name",
  "data": {
    // Event-specific data
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### QR Code Event

```json
{
  "type": "event",
  "event": "qr",
  "data": {
    "qr": "QR_CODE_DATA"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Ready Event

```json
{
  "type": "event",
  "event": "ready",
  "data": {},
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Message Event

```json
{
  "type": "event",
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "chatId": "chat_id",
      "content": "Hello, world!",
      "timestamp": "2023-01-01T00:00:00Z",
      "sender": {
        "id": "sender_id",
        "name": "Sender Name"
      },
      "hasMedia": false,
      "isGroup": false,
      "isForwarded": false,
      "mentionedIds": []
    }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Disconnected Event

```json
{
  "type": "event",
  "event": "disconnected",
  "data": {
    "reason": "Reason for disconnection"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Errors

Errors are sent as JSON objects with the following structure:

```json
{
  "type": "error",
  "id": "request_id",  // If the error is related to a specific request
  "error": "Error message",
  "timestamp": "2023-01-01T00:00:00Z"
}
```
