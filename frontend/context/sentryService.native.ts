/**
 * Sentry service - NATIVE version (iOS/Android)
 * Full Sentry crash reporting + performance monitoring
 */
import * as Sentry from '@sentry/react-native';

export const SentryAvailable = true;

const SENTRY_DSN = process.env.EXPO_PUBLIC_SENTRY_DSN || 'https://aed9d5abbb8fd2897cd3ee012f906cdd@o4511175037812736.ingest.us.sentry.io/4511175048757248';

export function initSentry() {
  try {
    Sentry.init({
      dsn: SENTRY_DSN,
      tracesSampleRate: __DEV__ ? 1.0 : 0.3,
      profilesSampleRate: __DEV__ ? 1.0 : 0.1,
      debug: __DEV__,
      enableNativeFramesTracking: !__DEV__,
      enableAutoPerformanceTracing: true,
      enabled: true,
      environment: __DEV__ ? 'development' : 'production',
      beforeSend(event) {
        // Optionally filter events
        return event;
      },
    });
    console.log('[Sentry] Initialized successfully');
  } catch (e) {
    console.log('[Sentry] Init error:', e);
  }
}

export function captureException(error: any) {
  Sentry.captureException(error);
}

export function captureMessage(message: string) {
  Sentry.captureMessage(message);
}

export function setUser(user: { id: string; email?: string; username?: string } | null) {
  if (user) {
    Sentry.setUser(user);
  } else {
    Sentry.setUser(null);
  }
}

export function wrapApp(component: any) {
  return Sentry.wrap(component);
}
