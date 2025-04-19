/**
 * WhatsApp Client Service
 * Handles connection and interaction with WhatsApp
 * 
 * @author Bruno Santos
 */

import { Client, LocalAuth, Message, MessageMedia } from 'whatsapp-web.js';
import qrcode from 'qrcode-terminal';
import { EventEmitter } from 'events';
import { logger } from '../utils/logger';
import { Contact, Chat, ChatMessage, MediaType } from '../types';

export interface WhatsAppClientOptions {
  dataPath: string;
  sessionName: string;
}

export class WhatsAppClient extends EventEmitter {
  private client: Client;
  private isReady: boolean = false;
  private messageCache: Map<string, ChatMessage> = new Map();
  
  constructor(options: WhatsAppClientOptions) {
    super();
    
    this.client = new Client({
      authStrategy: new LocalAuth({
        dataPath: options.dataPath,
        clientId: options.sessionName,
      }),
      puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
      },
    });
    
    this.setupEventListeners();
  }
  
  /**
   * Initialize the WhatsApp client
   */
  public async initialize(): Promise<void> {
    try {
      logger.info('Initializing WhatsApp client...');
      await this.client.initialize();
    } catch (error) {
      logger.error('Failed to initialize WhatsApp client', { error });
      throw error;
    }
  }
  
  /**
   * Destroy the WhatsApp client connection
   */
  public async destroy(): Promise<void> {
    try {
      logger.info('Destroying WhatsApp client...');
      await this.client.destroy();
      this.isReady = false;
    } catch (error) {
      logger.error('Error during WhatsApp client shutdown', { error });
      throw error;
    }
  }
  
  /**
   * Get the client ready state
   */
  public isClientReady(): boolean {
    return this.isReady;
  }
  
  /**
   * Get a list of contacts
   */
  public async getContacts(): Promise<Contact[]> {
    try {
      if (!this.isReady) {
        throw new Error('WhatsApp client is not ready');
      }
      
      const contacts = await this.client.getContacts();
      return contacts.map(contact => ({
        id: contact.id._serialized,
        name: contact.name || contact.pushname || '',
        number: contact.number,
        isGroup: contact.isGroup,
        isMyContact: contact.isMyContact,
      }));
    } catch (error) {
      logger.error('Failed to get contacts', { error });
      throw error;
    }
  }
  
  /**
   * Get a list of chats
   */
  public async getChats(): Promise<Chat[]> {
    try {
      if (!this.isReady) {
        throw new Error('WhatsApp client is not ready');
      }
      
      const chats = await this.client.getChats();
      return chats.map(chat => ({
        id: chat.id._serialized,
        name: chat.name,
        isGroup: chat.isGroup,
        timestamp: chat.timestamp ? new Date(chat.timestamp * 1000).toISOString() : '',
        unreadCount: chat.unreadCount,
      }));
    } catch (error) {
      logger.error('Failed to get chats', { error });
      throw error;
    }
  }
  
  /**
   * Get chat messages
   */
  public async getChatMessages(chatId: string, limit: number = 50): Promise<ChatMessage[]> {
    try {
      if (!this.isReady) {
        throw new Error('WhatsApp client is not ready');
      }
      
      const chat = await this.client.getChatById(chatId);
      const messages = await chat.fetchMessages({ limit });
      
      return messages.map(message => this.convertMessageToChatMessage(message));
    } catch (error) {
      logger.error('Failed to get chat messages', { error, chatId });
      throw error;
    }
  }
  
  /**
   * Send a message to a chat
   */
  public async sendMessage(chatId: string, content: string): Promise<ChatMessage> {
    try {
      if (!this.isReady) {
        throw new Error('WhatsApp client is not ready');
      }
      
      const chat = await this.client.getChatById(chatId);
      const sentMessage = await chat.sendMessage(content);
      
      const chatMessage = this.convertMessageToChatMessage(sentMessage);
      this.messageCache.set(chatMessage.id, chatMessage);
      
      return chatMessage;
    } catch (error) {
      logger.error('Failed to send message', { error, chatId });
      throw error;
    }
  }
  
  /**
   * Send a media message
   */
  public async sendMedia(
    chatId: string, 
    media: Buffer, 
    filename: string, 
    caption?: string, 
    mediaType?: MediaType
  ): Promise<ChatMessage> {
    try {
      if (!this.isReady) {
        throw new Error('WhatsApp client is not ready');
      }
      
      const mime = this.getMimeType(filename, mediaType);
      const messageMedia = new MessageMedia(mime, media.toString('base64'), filename);
      
      const chat = await this.client.getChatById(chatId);
      const sentMessage = await chat.sendMessage(messageMedia, { caption });
      
      const chatMessage = this.convertMessageToChatMessage(sentMessage);
      this.messageCache.set(chatMessage.id, chatMessage);
      
      return chatMessage;
    } catch (error) {
      logger.error('Failed to send media', { error, chatId });
      throw error;
    }
  }
  
  /**
   * Setup event listeners for the WhatsApp client
   */
  private setupEventListeners(): void {
    this.client.on('qr', (qr) => {
      logger.info('QR code received. Scan with WhatsApp to authenticate.');
      qrcode.generate(qr, { small: true });
      this.emit('qr', qr);
    });
    
    this.client.on('ready', () => {
      this.isReady = true;
      logger.info('WhatsApp client is ready');
      this.emit('ready');
    });
    
    this.client.on('authenticated', () => {
      logger.info('WhatsApp client authenticated');
      this.emit('authenticated');
    });
    
    this.client.on('auth_failure', (message) => {
      this.isReady = false;
      logger.error('WhatsApp authentication failed', { message });
      this.emit('auth_failure', message);
    });
    
    this.client.on('disconnected', (reason) => {
      this.isReady = false;
      logger.warn('WhatsApp client disconnected', { reason });
      this.emit('disconnected', reason);
    });
    
    this.client.on('message', (message) => {
      const chatMessage = this.convertMessageToChatMessage(message);
      this.messageCache.set(chatMessage.id, chatMessage);
      logger.debug('New message received', { 
        from: chatMessage.sender.name || chatMessage.sender.id,
        chatId: chatMessage.chatId
      });
      this.emit('message', chatMessage);
    });
  }
  
  /**
   * Convert WhatsApp message to ChatMessage format
   */
  private convertMessageToChatMessage(message: Message): ChatMessage {
    
    const msg = message as any;
    
    return {
      id: message.id._serialized,
      chatId: message.from,
      content: message.body,
      timestamp: new Date(message.timestamp * 1000).toISOString(),
      sender: {
        id: msg.author || message.from,
        name: msg._data?.notifyName || '',
      },
      hasMedia: msg.hasMedia || false,
      isGroup: msg.isGroup || false,
      isForwarded: msg.isForwarded || false,
      mentionedIds: Array.isArray(msg.mentionedIds) 
        ? msg.mentionedIds.map((id: any) => id._serialized || id.toString()) 
        : [],
    };
  }
  
  /**
   * Get MIME type based on filename and mediaType
   */
  private getMimeType(filename: string, mediaType?: MediaType): string {
    if (mediaType) {
      switch (mediaType) {
        case 'image': return 'image/jpeg';
        case 'video': return 'video/mp4';
        case 'audio': return 'audio/ogg';
        case 'document': return 'application/pdf';
        default: return 'application/octet-stream';
      }
    }
    
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'jpg':
      case 'jpeg': return 'image/jpeg';
      case 'png': return 'image/png';
      case 'gif': return 'image/gif';
      case 'mp4': return 'video/mp4';
      case 'mp3': return 'audio/mpeg';
      case 'ogg': return 'audio/ogg';
      case 'pdf': return 'application/pdf';
      case 'doc':
      case 'docx': return 'application/msword';
      case 'xls':
      case 'xlsx': return 'application/vnd.ms-excel';
      case 'ppt':
      case 'pptx': return 'application/vnd.ms-powerpoint';
      case 'txt': return 'text/plain';
      default: return 'application/octet-stream';
    }
  }
}
