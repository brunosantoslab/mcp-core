/**
 * Tests for WhatsApp Gateway Services
 *
 * @author Bruno Santos
 */

import { WhatsAppClient } from '../src/services/whatsapp-client';
import { Client, LocalAuth } from 'whatsapp-web.js';

// Mock whatsapp-web.js
jest.mock('whatsapp-web.js', () => {
  const initializeMock = jest.fn().mockResolvedValue(undefined);
  const destroyMock = jest.fn().mockResolvedValue(undefined);
  const getContactsMock = jest.fn().mockResolvedValue([
    {
      id: { _serialized: 'contact1' },
      name: 'Contact 1',
      number: '123456789',
      isGroup: false,
      isMyContact: true,
    },
  ]);
  const getChatsMock = jest.fn().mockResolvedValue([
    {
      id: { _serialized: 'chat1' },
      name: 'Chat 1',
      isGroup: false,
      timestamp: 1234567890, // Unix timestamp (seconds)
    },
  ]);
  const getChatByIdMock = jest.fn().mockResolvedValue({
    id: { _serialized: 'chat1' },
    fetchMessages: jest.fn().mockResolvedValue([
      {
        id: { _serialized: 'msg1' },
        body: 'Hello',
        from: 'sender1@s.whatsapp.net',
        timestamp: 1234567890, // Valid Unix timestamp (seconds)
        _data: { notifyName: 'Sender Name' },
      },
    ]),
    sendMessage: jest.fn().mockResolvedValue({
      id: { _serialized: 'msg2' },
      body: 'Hello World',
      from: 'me@s.whatsapp.net',
      fromMe: true,
      timestamp: 1234567890, // Valid Unix timestamp (seconds)
      _data: { notifyName: 'Me' },
    }),
  });

  const mockEventEmitter = {
    on: jest.fn(),
    emit: jest.fn(),
    removeAllListeners: jest.fn(),
  };

  const MockClient = jest.fn().mockImplementation(() => ({
    ...mockEventEmitter,
    initialize: initializeMock,
    destroy: destroyMock,
    getContacts: getContactsMock,
    getChats: getChatsMock,
    getChatById: getChatByIdMock,
  }));

  return {
    Client: MockClient,
    LocalAuth: jest.fn(),
    MessageMedia: jest.fn().mockImplementation((mime, data, filename) => ({})),
  };
});

// Mock qrcode-terminal
jest.mock('qrcode-terminal', () => ({
  generate: jest.fn(),
}));

describe('WhatsAppClient', () => {
  let whatsAppClient: WhatsAppClient;
  let initializeMock: jest.Mock;
  let destroyMock: jest.Mock;
  let getContactsMock: jest.Mock;
  let getChatsMock: jest.Mock;
  let getChatByIdMock: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    whatsAppClient = new WhatsAppClient({
      dataPath: './test-data',
      sessionName: 'test-session',
    });
    // Access mock functions directly
    const MockClient = jest.requireMock('whatsapp-web.js').Client;
    initializeMock = MockClient.mock.results[0].value.initialize;
    destroyMock = MockClient.mock.results[0].value.destroy;
    getContactsMock = MockClient.mock.results[0].value.getContacts;
    getChatsMock = MockClient.mock.results[0].value.getChats;
    getChatByIdMock = MockClient.mock.results[0].value.getChatById;
  });

  describe('initialize', () => {
    it('should initialize the WhatsApp client', async () => {
      await whatsAppClient.initialize();
      expect(initializeMock).toHaveBeenCalled();
    });
  });

  describe('destroy', () => {
    it('should destroy the WhatsApp client', async () => {
      await whatsAppClient.destroy();
      expect(destroyMock).toHaveBeenCalled();
    });
  });

  describe('getContacts', () => {
    it('should get contacts', async () => {
      (whatsAppClient as any).isReady = true;
      const contacts = await whatsAppClient.getContacts();
      expect(contacts).toHaveLength(1);
      expect(contacts[0]).toEqual({
        id: 'contact1',
        name: 'Contact 1',
        number: '123456789',
        isGroup: false,
        isMyContact: true,
      });
      expect(getContactsMock).toHaveBeenCalled();
    });

    it('should throw an error if client is not ready', async () => {
      (whatsAppClient as any).isReady = false;
      await expect(whatsAppClient.getContacts()).rejects.toThrow('WhatsApp client is not ready');
    });
  });

  describe('getChats', () => {
    it('should get chats', async () => {
      (whatsAppClient as any).isReady = true;
      const chats = await whatsAppClient.getChats();
      expect(chats).toHaveLength(1);
      expect(chats[0]).toEqual({
        id: 'chat1',
        name: 'Chat 1',
        isGroup: false,
        timestamp: '2009-02-13T23:31:30.000Z',
      });
      expect(getChatsMock).toHaveBeenCalled();
    });
  });

  describe('getChatMessages', () => {
    it('should get chat messages', async () => {
      (whatsAppClient as any).isReady = true;
      const messages = await whatsAppClient.getChatMessages('chat1');
      expect(messages).toHaveLength(1);
      expect(messages[0]).toMatchObject({
        id: 'msg1',
        content: 'Hello',
        timestamp: '2009-02-13T23:31:30.000Z',
        sender: { id: 'sender1@s.whatsapp.net', name: 'Sender Name' },
      });
      expect(getChatByIdMock).toHaveBeenCalledWith('chat1');
    });
  });

  describe('sendMessage', () => {
    it('should send a message', async () => {
      (whatsAppClient as any).isReady = true;
      const message = await whatsAppClient.sendMessage('chat1', 'Hello World');
      expect(message).toMatchObject({
        id: 'msg2',
        content: 'Hello World',
        timestamp: '2009-02-13T23:31:30.000Z',
        sender: { id: 'me@s.whatsapp.net', name: 'Me' },
      });
      expect(getChatByIdMock).toHaveBeenCalledWith('chat1');
    });
  });
});