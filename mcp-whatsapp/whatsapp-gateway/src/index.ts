/**
 * WhatsApp Gateway Service
 * Main entry point for the WhatsApp Gateway service
 * 
 * @author Bruno Santos
 */

import dotenv from 'dotenv';
import { WebSocketServer } from './services/websocket-server';
import { WhatsAppClient } from './services/whatsapp-client';
import { logger } from './utils/logger';

// Load environment variables
dotenv.config();

// Initialize WhatsApp client
const whatsAppClient = new WhatsAppClient({
  dataPath: process.env.WA_DATA_PATH || './.wwebjs_auth',
  sessionName: process.env.WA_SESSION_NAME || 'whatsapp-gateway-session',
});

// Initialize WebSocket server
const wsPort = parseInt(process.env.WS_PORT || '8090', 10);
const wsPath = process.env.WS_PATH || '/ws';
const webSocketServer = new WebSocketServer(wsPort, wsPath, whatsAppClient);

/**
 * Main function to start the WhatsApp Gateway service
 */
async function main() {
  try {
    logger.info('Starting WhatsApp Gateway service...');
    
    // Start WebSocket server
    await webSocketServer.start();
    logger.info(`WebSocket server started on port ${wsPort} with path ${wsPath}`);
    
    // Initialize WhatsApp client
    await whatsAppClient.initialize();
    logger.info('WhatsApp client initialized');
    
    // Handle process shutdown
    process.on('SIGINT', handleShutdown);
    process.on('SIGTERM', handleShutdown);
    
    logger.info('WhatsApp Gateway service is ready');
  } catch (error) {
    logger.error('Failed to start WhatsApp Gateway service', { error });
    process.exit(1);
  }
}

/**
 * Handle graceful shutdown of the service
 */
async function handleShutdown() {
  logger.info('Shutting down WhatsApp Gateway service...');
  
  try {
    // Close WebSocket server
    await webSocketServer.stop();
    logger.info('WebSocket server stopped');
    
    // Disconnect WhatsApp client
    await whatsAppClient.destroy();
    logger.info('WhatsApp client disconnected');
    
    logger.info('WhatsApp Gateway service shutdown complete');
    process.exit(0);
  } catch (error) {
    logger.error('Error during shutdown', { error });
    process.exit(1);
  }
}

// Start the service
main();
