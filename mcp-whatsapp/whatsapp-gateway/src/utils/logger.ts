/**
 * Logger utility for the WhatsApp Gateway
 * 
 * @author Bruno Santos
 */

import winston from 'winston';
import path from 'path';
import fs from 'fs';

// Ensure logs directory exists
const logDir = process.env.LOG_FILE_PATH 
  ? path.dirname(process.env.LOG_FILE_PATH)
  : './logs';

if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Create a custom log format
const logFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ level, message, timestamp, ...meta }) => {
    const metaString = Object.keys(meta).length 
      ? `\n${JSON.stringify(meta, null, 2)}` 
      : '';
    return `${timestamp} [${level.toUpperCase()}]: ${message}${metaString}`;
  })
);

// Initialize the logger
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { service: 'whatsapp-gateway' },
  transports: [
    // Console logging
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        logFormat
      ),
    }),
    
    // File logging
    new winston.transports.File({
      filename: process.env.LOG_FILE_PATH || path.join(logDir, 'gateway.log'),
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
  ],
});

// Add error handler
logger.on('error', (error) => {
  console.error('Logger error:', error);
});

export default logger;
