/**
 * Type definitions for the WhatsApp Gateway
 * 
 * @author Bruno Santos
 */

// WhatsApp Types
export interface Contact {
  id: string;
  name: string;
  number: string;
  isGroup: boolean;
  isMyContact: boolean;
}

export interface Chat {
  id: string;
  name: string;
  isGroup: boolean;
  timestamp: string;
  unreadCount: number;
}

export interface Sender {
  id: string;
  name: string;
}

export interface ChatMessage {
  id: string;
  chatId: string;
  content: string;
  timestamp: string;
  sender: Sender;
  hasMedia: boolean;
  isGroup: boolean;
  isForwarded: boolean;
  mentionedIds: string[];
}

export type MediaType = 'image' | 'video' | 'audio' | 'document';

// Gateway Message Types
export enum GatewayMessageType {
  COMMAND = 'command',
  RESPONSE = 'response',
  EVENT = 'event',
  ERROR = 'error',
}

export type GatewayEvent = 
  | 'qr'
  | 'ready'
  | 'authenticated'
  | 'auth_failure'
  | 'disconnected'
  | 'message';

export type GatewayCommand = 
  | 'getContacts'
  | 'getChats'
  | 'getChatMessages'
  | 'sendMessage'
  | 'sendMedia';

export interface GatewayCommandMessage {
  type: GatewayMessageType.COMMAND;
  id: string;
  command: GatewayCommand;
  data?: Record<string, unknown>;
  timestamp?: string;
}

export interface GatewayResponseMessage {
  type: GatewayMessageType.RESPONSE | GatewayMessageType.EVENT;
  id?: string;
  command?: string;
  event?: GatewayEvent;
  data: any;
  timestamp: string;
}

export interface ErrorResponse {
  type: GatewayMessageType.ERROR;
  id?: string;
  error: string;
  timestamp: string;
}
