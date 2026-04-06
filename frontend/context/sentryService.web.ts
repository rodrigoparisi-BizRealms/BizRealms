/**
 * Sentry service - WEB version (lightweight browser reporting)
 */

export const SentryAvailable = false;

export function initSentry() {
  // On web preview, we use console.error as fallback
  console.log('[Sentry] Web fallback - errors will be logged to console');
}

export function captureException(error: any) {
  console.error('[Sentry:web]', error);
}

export function captureMessage(message: string) {
  console.log('[Sentry:web]', message);
}

export function setUser(user: { id: string; email?: string; username?: string } | null) {
  // no-op on web
}

export function wrapApp(component: any) {
  return component;
}
