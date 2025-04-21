/**
 * WebSocket Server
 * Handles communication with the MCP WhatsApp Server
 * 
 * @author Bruno Santos
 */

import WebSocket, { Server } from 'ws';
import { createServer, Server as HttpServer } from 'http';
import { logger } from '../utils/logger';
import { WhatsAppClient } from './whatsapp-client';
import { 
  GatewayEvent, 
  GatewayMessageType, 
  GatewayCommandMessage, 
  GatewayResponseMessage,
  ErrorResponse
} from '../types';

export class WebSocketServer {
  private server: HttpServer;
  private wss: Server;
  private clients: Set<WebSocket> = new Set();
  private whatsAppClient: WhatsAppClient;
  private wsPath: string;
  
  constructor(port: number, path: string, whatsAppClient: WhatsAppClient) {
    this.whatsAppClient = whatsAppClient;
    this.wsPath = path;
    
    // Create HTTP server
    this.server = createServer();
    
    // Create WebSocket server
    this.wss = new Server({ 
      server: this.server,
      path
    });
    
    // Configure the server to listen on the specified port
    this.server.listen(port);
    
    this.setupEventListeners();
  }
  
  /**
   * Start the WebSocket server
   */
  public async start(): Promise<void> {
    return new Promise<void>((resolve) => {
      this.server.once('listening', () => {
        logger.info(`WebSocket server started`);
        resolve();
      });
    });
  }
  
  /**
   * Stop the WebSocket server
   */
  public async stop(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      // Close all WebSocket connections
      for (const client of this.clients) {
        client.terminate();
      }
      this.clients.clear();
      
      // Close the WebSocket server
      this.wss.close((error) => {
        if (error) {
          logger.error('Error closing WebSocket server', { error });
          reject(error);
        } else {
          // Close the HTTP server
          this.server.close((err) => {
            if (err) {
              logger.error('Error closing HTTP server', { err });
              reject(err);
            } else {
              logger.info('WebSocket server stopped');
              resolve();
            }
          });
        }
      });
    });
  }
  
  /**
   * Set up event listeners for the WebSocket server
   */
  private setupEventListeners(): void {
    // WebSocket connection event
    this.wss.on('connection', (ws, req) => {
      logger.info(`New WebSocket connection from ${req.socket.remoteAddress}`);
      this.clients.add(ws);
      
      // Handle messages from clients
      ws.on('message', (data) => {
        this.handleMessage(ws, data.toString());
      });
      
      // Handle client disconnection
      ws.on('close', () => {
        logger.info('WebSocket connection closed');
        this.clients.delete(ws);
      });
      
      // Handle connection errors
      ws.on('error', (error) => {
        logger.error('WebSocket error', { error });
        this.clients.delete(ws);
      });
      
      // Send ready status if WhatsApp client is already authenticated
      if (this.whatsAppClient.isClientReady()) {
        this.sendEvent(ws, 'ready', {});
      }
    });
    
    // Forward WhatsApp events to WebSocket clients
    this.whatsAppClient.on('qr', (qr) => {
      this.broadcast('qr', { qr });
    });
    
    this.whatsAppClient.on('ready', () => {
      this.broadcast('ready', {});
    });
    
    this.whatsAppClient.on('authenticated', () => {
      this.broadcast('authenticated', {});
    });
    
    this.whatsAppClient.on('auth_failure', (message) => {
      this.broadcast('auth_failure', { message });
    });
    
    this.whatsAppClient.on('disconnected', (reason) => {
      this.broadcast('disconnected', { reason });
    });
    
    this.whatsAppClient.on('message', (message) => {
      this.broadcast('message', { message });
    });
  }
  
  /**
   * Handle incoming WebSocket messages
   */
  private async handleMessage(ws: WebSocket, data: string): Promise<void> {
    try {
      const message = JSON.parse(data) as GatewayCommandMessage;
      
      // Validate message format
      if (!message.type || !message.command) {
        return this.sendError(ws, 'Invalid message format');
      }
      
      // Handle different command types
      switch (message.command) {
        case 'getContacts':
          await this.handleGetContacts(ws, message);
          break;
        
        case 'getChats':
          await this.handleGetChats(ws, message);
          break;
        
        case 'getChatMessages':
          await this.handleGetChatMessages(ws, message);
          break;
        
        case 'sendMessage':
          await this.handleSendMessage(ws, message);
          break;
          
        case 'sendMedia':
          await this.handleSendMedia(ws, message);
          break;
          
        default:
          this.sendError(ws, `Unknown command: ${message.command}`);
      }
    } catch (error) {
      logger.error('Error handling WebSocket message', { error });
      this.sendError(ws, 'Error processing command');
    }
  }
  
  /**
   * Handle the getContacts command
   */
  private async handleGetContacts(ws: WebSocket, message: GatewayCommandMessage): Promise<void> {
    try {
      const contacts = await this.whatsAppClient.getContacts();
      this.sendResponse(ws, message.id, 'getContacts', { contacts });
    } catch (error) {
      logger.error('Error handling getContacts command', { error });
      this.sendError(ws, 'Failed to get contacts', message.id);
    }
  }
  
  /**
   * Handle the getChats command
   */
  private async handleGetChats(ws: WebSocket, message: GatewayCommandMessage): Promise<void> {
    try {
      const chats = await this.whatsAppClient.getChats();
      this.sendResponse(ws, message.id, 'getChats', { chats });
    } catch (error) {
      logger.error('Error handling getChats command', { error });
      this.sendError(ws, 'Failed to get chats', message.id);
    }
  }
  
  /**
   * Handle the getChatMessages command
   */
  private async handleGetChatMessages(ws: WebSocket, message: GatewayCommandMessage): Promise<void> {
    try {
      if (!message.data || !message.data.chatId) {
        return this.sendError(ws, 'Missing chatId parameter', message.id);
      }
      
      const chatId = message.data.chatId as string;
      const limit = message.data.limit ? parseInt(message.data.limit as string, 10) : 50;
      
      const messages = await this.whatsAppClient.getChatMessages(chatId, limit);
      this.sendResponse(ws, message.id, 'getChatMessages', { messages });
    } catch (error) {
      logger.error('Error handling getChatMessages command', { error });
      this.sendError(ws, 'Failed to get chat messages', message.id);
    }
  }
  
  /**
   * Handle the sendMessage command
   */
  private async handleSendMessage(ws: WebSocket, message: GatewayCommandMessage): Promise<void> {
    try {
      if (!message.data || !message.data.chatId || !message.data.content) {
        return this.sendError(ws, 'Missing chatId or content parameter', message.id);
      }
      
      const chatId = message.data.chatId as string;
      const content = message.data.content as string;
      
      const sentMessage = await this.whatsAppClient.sendMessage(chatId, content);
      this.sendResponse(ws, message.id, 'sendMessage', { message: sentMessage });
    } catch (error) {
      logger.error('Error handling sendMessage command', { error });
      this.sendError(ws, 'Failed to send message', message.id);
    }
  }
  

  private async handleSendMedia(ws: WebSocket, message: GatewayCommandMessage): Promise<void> {
    try {
      if (!message.data || !message.data.chatId || !message.data.media || !message.data.filename) {
        return this.sendError(ws, 'Missing required parameters for sendMedia', message.id);
      }
      
      const chatId = message.data.chatId as string;
      let mediaBase64 = message.data.media as string;
      const filename = message.data.filename as string;
      const caption = message.data.caption as string | undefined;
      const mediaType = message.data.mediaType as any;
      
      // Handle data URLs (e.g., from Claude or browser)
      if (mediaBase64.startsWith('data:')) {
        const parts = mediaBase64.split(',');
        if (parts.length > 1) {
          mediaBase64 = parts[1];
          logger.info('Removed data URL prefix from media string');
        }
      }
      
      const mediaBuffer = Buffer.from(mediaBase64, 'base64');

      logger.info('Preparing to send media', { 
        chatId, 
        filename,
        mediaType,
        bufferSize: mediaBuffer.length,
        hasCaption: !!caption
      });

      try {
        const sentMessage = await this.whatsAppClient.sendMedia(
          chatId, 
          mediaBuffer, 
          filename, 
          caption, 
          mediaType
        );
        
        this.sendResponse(ws, message.id, 'sendMedia', { message: sentMessage });
      } catch (innerError: unknown) {
        const errorDetails = {
          message: innerError instanceof Error ? innerError.message : String(innerError),
          stack: innerError instanceof Error ? innerError.stack : undefined,
          name: innerError instanceof Error ? innerError.name : undefined
        };
        
        logger.error('WhatsApp client sendMedia failed', { 
          error: innerError, 
          errorDetails,
          chatId
        });
        
        // Special handling for the specific Puppeteer error
        if (errorDetails.message?.includes('Evaluation failed: a')) {
          logger.info('Detected specific Puppeteer error, attempting alternative approach');
          
          try {
            // Try with document type and sendMediaAsDocument option
            const sentMessage = await this.whatsAppClient.sendMediaAsDocument(
              chatId, 
              mediaBuffer, 
              filename, 
              caption
            );
            
            logger.info('Successfully sent media using alternative approach');
            this.sendResponse(ws, message.id, 'sendMedia', { message: sentMessage });
            return;
          } catch (altError: unknown) {
            const altErrorDetails = {
              message: altError instanceof Error ? altError.message : String(altError),
              stack: altError instanceof Error ? altError.stack : undefined,
              name: altError instanceof Error ? altError.name : undefined
            };
            
            logger.error('Alternative approach also failed', { 
              error: altError, 
              errorDetails: altErrorDetails 
            });
            
            // Continue with normal error response
          }
        }
        
        this.sendError(ws, `Failed to send media: ${errorDetails.message}`, message.id);
      }
    } catch (error: unknown) {
      const errorDetails = {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        name: error instanceof Error ? error.name : undefined
      };
      
      logger.error('Error handling sendMedia command', { 
        error, 
        errorDetails
      });
      this.sendError(ws, 'Failed to process media command', message.id);
    }
  }
  
  /**
   * Send an event to a specific client
   */
  private sendEvent(ws: WebSocket, event: GatewayEvent, data: any): void {
    const message: GatewayResponseMessage = {
      type: GatewayMessageType.EVENT,
      event,
      data,
      timestamp: new Date().toISOString(),
    };
    
    ws.send(JSON.stringify(message));
  }
  
  /**
   * Send a response to a command
   */
  private sendResponse(ws: WebSocket, requestId: string, command: string, data: any): void {
    const response: GatewayResponseMessage = {
      type: GatewayMessageType.RESPONSE,
      id: requestId,
      command,
      data,
      timestamp: new Date().toISOString(),
    };
    
    ws.send(JSON.stringify(response));
  }
  
  /**
   * Send an error response
   */
  private sendError(ws: WebSocket, message: string, requestId?: string): void {
    const error: ErrorResponse = {
      type: GatewayMessageType.ERROR,
      id: requestId,
      error: message,
      timestamp: new Date().toISOString(),
    };
    
    ws.send(JSON.stringify(error));
  }
  
  /**
   * Broadcast an event to all connected clients
   */
  private broadcast(event: GatewayEvent, data: any): void {
    const message: GatewayResponseMessage = {
      type: GatewayMessageType.EVENT,
      event,
      data,
      timestamp: new Date().toISOString(),
    };
    
    const payload = JSON.stringify(message);
    
    for (const client of this.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(payload);
      }
    }
  }
}