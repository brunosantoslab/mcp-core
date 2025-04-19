/**
 * Tests for WhatsApp Gateway Services
 * 
 * @author Bruno Santos
 */

import { WhatsAppClient } from '../src/services/whatsapp-client';
import { Client, LocalAuth } from 'whatsapp-web.js';

// Mock whatsapp-web.js
jest.mock('whatsapp-web.js', () => {
  const mockEventEmitter = {
    on: jest.fn(),
    emit: jest.fn(),
    removeAllListeners: jest.fn(),
  };
  
  const mockClient = jest.fn().mockImplementation(() => ({
    ...mockEventEmitter,
    initialize: jest.fn().mockResolvedValue(undefined),
    destroy: jest.fn().mockResolvedValue(undefined),
    getContacts: jest.fn().mockResolvedValue([
      {
        id: { _serialized: 'contact1' },
        name: 'Contact 1',
        pushname: 'Contact 1 Push',
        number: '123456789',
        isGroup: false,
        isMyContact: true,
      },
    ]),
    getChats: jest.fn().mockResolvedValue([
      {
        id: { _serialized: 'chat1' },
        name: 'Chat 1',
        isGroup: false,
        timestamp: 1610000000,
        unreadCount: 0,
      },
    ]),
    getChatById: jest.fn().mockResolvedValue({
      fetchMessages: jest.fn().mockResolvedValue([
        {
          id: { _serialized: 'msg1' },
          from: 'sender1',
          body: 'Hello',
          timestamp: 1610000000,
          author: 'sender1',
          _data: { notifyName: 'Sender Name' },
          hasMedia: false,
          isGroup: false,
          isForwarded: false,
          mentionedIds: [],
        },
      ]),
      sendMessage: jest.fn().mockImplementation((content) => ({
        id: { _serialized: 'newMsg1' },
        from: 'me',
        body: content,
        timestamp: Date.now() / 1000,
        author: 'me',
        _data: { notifyName: 'Me' },
        hasMedia: false,
        isGroup: false,
        isForwarded: false,
        mentionedIds: [],
      })),
    }),
  }));
  
  return {
    Client: mockClient,
    LocalAuth: jest.fn(),
    MessageMedia: jest.fn().mockImplementation((mime, data, filename) => ({
      mimetype: mime,
      data,
      filename,
    })),
  };
});

// Mock qrcode-terminal
jest.mock('qrcode-terminal', () => ({
  generate: jest.fn(),
}));

describe('WhatsAppClient', () => {
  let whatsAppClient: WhatsAppClient;
  
  beforeEach(() => {
    jest.clearAllMocks();
    whatsAppClient = new WhatsAppClient({
      dataPath: './test-data',
      sessionName: 'test-session',
    });
  });
  
  describe('initialize', () => {
    it('should initialize the WhatsApp client', async () => {
      await whatsAppClient.initialize();
      expect(Client.prototype.initialize).toHaveBeenCalled();
    });
  });
  
  describe('destroy', () => {
    it('should destroy the WhatsApp client', async () => {
      await whatsAppClient.destroy();
      expect(Client.prototype.destroy).toHaveBeenCalled();
    });
  });
  
  describe('getContacts', () => {
    it('should get contacts', async () => {
      // Set the client as ready
      (whatsAppClient as any).isReady = true;
      
      const contacts = await whatsAppClient.getContacts();
      
      expect(contacts).toHaveLength(1);
      expect(contacts[0].id).toBe('contact1');
      expect(contacts[0].name).toBe('Contact 1');
      expect(contacts[0].number).toBe('123456789');
      expect(contacts[0].isGroup).toBe(false);
      expect(contacts[0].isMyContact).toBe(true);
    });
    
    it('should throw an error if client is not ready', async () => {
      // Set the client as not ready
      (whatsAppClient as any).isReady = false;
      
      await expect(whatsAppClient.getContacts()).rejects.toThrow('WhatsApp client is not ready');
    });
  });
  
  describe('getChats', () => {
    it('should get chats', async () => {
      // Set the client as ready
      (whatsAppClient as any).isReady = true;
      
      const chats = await whatsAppClient.getChats();
      
      expect(chats).toHaveLength(1);
      expect(chats[0].id).toBe('chat1');
      expect(chats[0].name).toBe('Chat 1');
      expect(chats[0].isGroup).toBe(false);
      expect(typeof chats[0].timestamp).toBe('string');
      expect(chats[0].unreadCount).toBe(0);
    });
  });
  
  describe('getChatMessages', () => {
    it('should get chat messages', async () => {
      // Set the client as ready
      (whatsAppClient as any).isReady = true;
      
      const messages = await whatsAppClient.getChatMessages('chat1');
      
      expect(messages).toHaveLength(1);
      expect(messages[0].id).toBe('msg1');
      expect(messages[0].content).toBe('Hello');
      expect(messages[0].sender.id).toBe('sender1');
      expect(messages[0].sender.name).toBe('Sender Name');
    });
  });
  
  describe('sendMessage', () => {
    it('should send a message', async () => {
      // Set the client as ready
      (whatsAppClient as any).isReady = true;
      
      const message = await whatsAppClient.sendMessage('chat1', 'Hello World');
      
      expect(message.content).toBe('Hello World');
      expect(message.sender.id).toBe('me');
    });
  });
});
