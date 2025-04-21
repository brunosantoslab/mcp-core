/**
 * Error handler utility for the WhatsApp Gateway
 * 
 * @author Bruno Santos
 */

import { logger } from './logger';

/**
 * Custom error class for WhatsApp Gateway errors
 */
export class GatewayError extends Error {
  public code: string;
  public details?: any;

  constructor(message: string, code: string, details?: any) {
    super(message);
    this.name = 'GatewayError';
    this.code = code;
    this.details = details;
  }
}

/**
 * Handle and log errors
 */
export function handleError(error: any, context?: string): GatewayError {
  // If it's already a GatewayError, just log it
  if (error instanceof GatewayError) {
    logger.error(`${context || 'Error'}: ${error.message}`, {
      code: error.code,
      details: error.details,
      stack: error.stack,
    });
    return error;
  }

  // Convert other errors to GatewayError
  const message = error.message || 'An unknown error occurred';
  const code = error.code || 'UNKNOWN_ERROR';
  
  const gatewayError = new GatewayError(message, code, {
    originalError: error.toString(),
  });

  logger.error(`${context || 'Error'}: ${message}`, {
    code,
    stack: error.stack,
    originalError: error,
  });

  return gatewayError;
}

/**
 * Create an authentication error
 */
export function createAuthError(message: string): GatewayError {
  return new GatewayError(message, 'AUTH_ERROR');
}

/**
 * Create a validation error
 */
export function createValidationError(message: string, details?: any): GatewayError {
  return new GatewayError(message, 'VALIDATION_ERROR', details);
}

/**
 * Create a WhatsApp API error
 */
export function createWhatsAppError(message: string, details?: any): GatewayError {
  return new GatewayError(message, 'WHATSAPP_ERROR', details);
}

/**
 * Create a not found error
 */
export function createNotFoundError(what: string): GatewayError {
  return new GatewayError(`${what} not found`, 'NOT_FOUND_ERROR');
}

/**
 * Create a connection error
 */
export function createConnectionError(message: string): GatewayError {
  return new GatewayError(message, 'CONNECTION_ERROR');
}

/**
 * Create a rate limit error
 */
export function createRateLimitError(): GatewayError {
  return new GatewayError('Rate limit exceeded', 'RATE_LIMIT_ERROR');
}
