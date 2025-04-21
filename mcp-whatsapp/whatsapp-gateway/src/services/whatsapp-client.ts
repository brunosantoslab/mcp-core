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
      const baseTimeout = 30000; 
      const timeoutMs = Math.max(baseTimeout, Math.min(300000, media.length / 10));
      
      logger.info(`Setting timeout of ${timeoutMs}ms based on media size of ${(media.length/1024).toFixed(2)}KB`);

      if (!this.isReady) {
        logger.error('WhatsApp client not ready when attempting to send media');
        throw new Error('WhatsApp client is not ready');
      }

      // Automatically detect media type if not provided
      if (!mediaType) {
        const ext = filename.split('.').pop()?.toLowerCase() || '';
        if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
          mediaType = 'image';
          logger.info(`Auto-detected media type as 'image' based on extension: ${ext}`);
        } else if (['mp4', 'avi', 'mov', 'webm'].includes(ext)) {
          mediaType = 'video';
          logger.info(`Auto-detected media type as 'video' based on extension: ${ext}`);
        } else if (['mp3', 'wav', 'ogg', 'aac'].includes(ext)) {
          mediaType = 'audio';
          logger.info(`Auto-detected media type as 'audio' based on extension: ${ext}`);
        } else {
          mediaType = 'document';
          logger.info(`Auto-detected media type as 'document' based on extension: ${ext}`);
        }
      }
  
      const mime = this.getMimeType(filename, mediaType);
      const ext = filename.split('.').pop()?.toLowerCase() || '';
      
      logger.info('Media preparation details', { 
        mime, 
        mediaType, 
        filename,
        extension: ext,
        mediaSizeBytes: media.length
      });
      
      if (media.length < 100) {
        logger.error('Media buffer too small - likely corrupted or empty', { 
          size: media.length,
          filename
        });
        throw new Error('Media file appears to be corrupted or empty (buffer too small)');
      }
      
      const MAX_SIZE = 16 * 1024 * 1024;
      if (media.length > MAX_SIZE) {
        logger.error('Media exceeds WhatsApp size limit', { 
          size: media.length,
          maxSize: MAX_SIZE,
          filename
        });
        throw new Error(`Media exceeds WhatsApp size limit (16MB). Current size: ${(media.length / (1024 * 1024)).toFixed(2)}MB`);
      }
      
      if (mediaType === 'image' && !['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
        logger.warn('Possible mismatch between image mediaType and file extension', {
          mediaType,
          extension: ext,
          mime
        });
      }
      
      const mediaBase64 = media.toString('base64');
      const messageMedia = new MessageMedia(mime, mediaBase64, filename);

      logger.info(`Attempting to get chat with ID: ${chatId}`);
      const chat = await this.client.getChatById(chatId);
      
      logger.info('Sending media message', { 
        chatId, 
        hasCaption: !!caption,
        mimeType: mime
      });
      
      try {
        const sentMessage = await this.timeoutPromise(
          chat.sendMessage(messageMedia, { caption }),
          timeoutMs,
          `Sending media timed out after ${timeoutMs/1000} seconds`
        );

        logger.info('Media message sent successfully');
        
        const chatMessage = this.convertMessageToChatMessage(sentMessage);
        this.messageCache.set(chatMessage.id, chatMessage);
        
        return chatMessage;
      } catch (sendError) {
        logger.error('First attempt to send media failed', {
          error: sendError,
          errorMessage: sendError instanceof Error ? sendError.message : String(sendError),
          chatId,
          mime
        });
        
        if (mediaType === 'image') {
          logger.info('Attempting to send image as document instead');
          try {
            const docMedia = new MessageMedia('application/octet-stream', mediaBase64, filename);
            const sentMessage = await chat.sendMessage(docMedia, { 
              caption, 
              sendMediaAsDocument: true 
            });
            
            logger.info('Successfully sent media as document');
            const chatMessage = this.convertMessageToChatMessage(sentMessage);
            this.messageCache.set(chatMessage.id, chatMessage);
            
            return chatMessage;
          } catch (docError) {
            logger.error('Failed to send media as document too', {
              error: docError,
              errorMessage: docError instanceof Error ? docError.message : String(docError)
            });
            throw sendError;
          }
        }
        
        throw sendError;
      }
    } catch (error) {
      const errorDetails = {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        name: error instanceof Error ? error.name : undefined
      };
      
      logger.error('Failed to send media', { 
        error, 
        errorDetails,
        chatId,
        filename
      });
      
      throw error;
    }
  }

  /**
   * Send media as document (alternative method for problematic media)
   */
  public async sendMediaAsDocument(
    chatId: string, 
    media: Buffer, 
    filename: string, 
    caption?: string
  ): Promise<ChatMessage> {
    try {
      if (!this.isReady) {
        throw new Error('WhatsApp client is not ready');
      }
      
      logger.info('Attempting to send media as document with alternative method', {
        chatId,
        filename,
        mediaSize: media.length
      });
      
      // Special handling for problematic media
      // Use generic MIME type to avoid Puppeteer issues
      const docMedia = new MessageMedia('application/octet-stream', media.toString('base64'), filename);
      
      const chat = await this.client.getChatById(chatId);
      
      // Send with explicit document option
      const sentMessage = await this.timeoutPromise(
        chat.sendMessage(docMedia, { 
          caption, 
          sendMediaAsDocument: true 
        }),
        60000, // 1 minute timeout
        'Sending media as document timed out'
      );
      
      logger.info('Successfully sent media as document with alternative method');
      const chatMessage = this.convertMessageToChatMessage(sentMessage);
      this.messageCache.set(chatMessage.id, chatMessage);
      
      return chatMessage;
    } catch (error) {
      const errorDetails = {
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        name: error instanceof Error ? error.name : undefined
      };
      
      logger.error('Failed to send media as document with alternative method', { 
        error, 
        errorDetails,
        chatId,
        filename
      });
      
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
    // Get file extension
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    
    // If mediaType is provided, use it as a primary classifier
    if (mediaType) {
      switch (mediaType) {
        case 'image':
          // Determine specific image type based on extension
          switch (ext) {
            case 'png': return 'image/png';
            case 'gif': return 'image/gif';
            case 'webp': return 'image/webp';
            case 'svg': return 'image/svg+xml';
            case 'bmp': return 'image/bmp';
            case 'tiff':
            case 'tif': return 'image/tiff';
            case 'ico': return 'image/x-icon';
            default: return 'image/jpeg'; // Default for jpg, jpeg, or unknown
          }
        
        case 'video':
          // Determine specific video type
          switch (ext) {
            case 'mp4': return 'video/mp4';
            case 'webm': return 'video/webm';
            case 'avi': return 'video/x-msvideo';
            case 'wmv': return 'video/x-ms-wmv';
            case 'flv': return 'video/x-flv';
            case 'mov': return 'video/quicktime';
            case '3gp': return 'video/3gpp';
            case 'mkv': return 'video/x-matroska';
            default: return 'video/mp4'; // Default
          }
        
        case 'audio':
          // Determine specific audio type
          switch (ext) {
            case 'mp3': return 'audio/mpeg';
            case 'wav': return 'audio/wav';
            case 'ogg': return 'audio/ogg';
            case 'flac': return 'audio/flac';
            case 'm4a': return 'audio/mp4';
            case 'aac': return 'audio/aac';
            case 'wma': return 'audio/x-ms-wma';
            case 'opus': return 'audio/opus';
            default: return 'audio/mpeg'; // Default
          }
        
        case 'document':
          // Default for document based on extension
          switch (ext) {
            case 'pdf': return 'application/pdf';
            case 'doc':
            case 'docx': return 'application/msword';
            case 'xls':
            case 'xlsx': return 'application/vnd.ms-excel';
            case 'ppt':
            case 'pptx': return 'application/vnd.ms-powerpoint';
            case 'txt': return 'text/plain';
            case 'rtf': return 'application/rtf';
            case 'csv': return 'text/csv';
            case 'xml': return 'application/xml';
            case 'json': return 'application/json';
            case 'zip': return 'application/zip';
            case 'rar': return 'application/x-rar-compressed';
            case '7z': return 'application/x-7z-compressed';
            case 'tar': return 'application/x-tar';
            case 'gz': 
            case 'gzip': return 'application/gzip';
            default: return 'application/octet-stream'; // Default for unknown
          }
        
        default:
          // If mediaType is unknown, fallback to extension-based detection
          break;
      }
    }
    
    // If we get here, either no mediaType was provided or it wasn't recognized
    // Determine MIME type based on file extension
    switch (ext) {
      // Images
      case 'jpg':
      case 'jpeg': return 'image/jpeg';
      case 'png': return 'image/png';
      case 'gif': return 'image/gif';
      case 'webp': return 'image/webp';
      case 'svg': return 'image/svg+xml';
      case 'bmp': return 'image/bmp';
      case 'tiff':
      case 'tif': return 'image/tiff';
      case 'ico': return 'image/x-icon';
      
      // Videos
      case 'mp4': return 'video/mp4';
      case 'webm': return 'video/webm';
      case 'avi': return 'video/x-msvideo';
      case 'wmv': return 'video/x-ms-wmv';
      case 'flv': return 'video/x-flv';
      case 'mov': return 'video/quicktime';
      case '3gp': return 'video/3gpp';
      case 'mkv': return 'video/x-matroska';
      
      // Audio
      case 'mp3': return 'audio/mpeg';
      case 'wav': return 'audio/wav';
      case 'ogg': return 'audio/ogg';
      case 'flac': return 'audio/flac';
      case 'm4a': return 'audio/mp4';
      case 'aac': return 'audio/aac';
      case 'wma': return 'audio/x-ms-wma';
      case 'opus': return 'audio/opus';
      
      // Documents
      case 'pdf': return 'application/pdf';
      case 'doc': return 'application/msword';
      case 'docx': return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      case 'xls': return 'application/vnd.ms-excel';
      case 'xlsx': return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      case 'ppt': return 'application/vnd.ms-powerpoint';
      case 'pptx': return 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
      case 'txt': return 'text/plain';
      case 'rtf': return 'application/rtf';
      case 'csv': return 'text/csv';
      case 'html': return 'text/html';
      case 'css': return 'text/css';
      case 'js': return 'application/javascript';
      case 'xml': return 'application/xml';
      case 'json': return 'application/json';
      
      // Archives
      case 'zip': return 'application/zip';
      case 'rar': return 'application/x-rar-compressed';
      case '7z': return 'application/x-7z-compressed';
      case 'tar': return 'application/x-tar';
      case 'gz': return 'application/gzip';
      
      // Fonts
      case 'ttf': return 'font/ttf';
      case 'otf': return 'font/otf';
      case 'woff': return 'font/woff';
      case 'woff2': return 'font/woff2';
      
      // Other common types
      case 'apk': return 'application/vnd.android.package-archive';
      case 'exe': return 'application/x-msdownload';
      case 'dll': return 'application/x-msdownload';
      case 'iso': return 'application/x-iso9660-image';
      case 'vcf': return 'text/vcard';
      case 'ics': return 'text/calendar';
      
      // Default fallback for unknown types
      default:
        logger.warn(`Unknown file extension: ${ext}, defaulting to octet-stream`);
        return 'application/octet-stream';
    }
  }

  private async timeoutPromise<T>(promise: Promise<T>, ms: number, errorMessage: string): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        setTimeout(() => reject(new Error(errorMessage)), ms);
      })
    ]);
  }
}
