import { useState, useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export function usePushNotifications(token: string | null) {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [notification, setNotification] = useState<Notifications.Notification | null>(null);
  const notificationListener = useRef<Notifications.EventSubscription>();
  const responseListener = useRef<Notifications.EventSubscription>();

  useEffect(() => {
    if (!token) return; // No auth token, don't register

    registerForPushNotifications().then(async (pushToken) => {
      if (pushToken) {
        setExpoPushToken(pushToken);
        // Register token with backend
        try {
          await axios.post(
            `${EXPO_PUBLIC_BACKEND_URL}/api/push/register`,
            { push_token: pushToken, platform: Platform.OS },
            { headers: { Authorization: `Bearer ${token}` } }
          );
        } catch (e) {
          console.log('Push token registration error:', e);
        }
      }
    });

    // Listen for incoming notifications
    notificationListener.current = Notifications.addNotificationReceivedListener((notification) => {
      setNotification(notification);
    });

    // Listen for notification responses (user tapping notification)
    responseListener.current = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data;
      console.log('Notification tapped, data:', data);
      // Handle navigation based on notification data
    });

    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, [token]);

  return { expoPushToken, notification };
}

async function registerForPushNotifications(): Promise<string | null> {
  // Push notifications only work on physical devices
  if (Platform.OS === 'web') {
    console.log('Push notifications not supported on web');
    return null;
  }

  if (!Device.isDevice) {
    console.log('Push notifications require physical device');
    return null;
  }

  try {
    // Check existing permission
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    // Request permission if not granted
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Push notification permission denied');
      return null;
    }

    // Get push token
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const tokenResult = await Notifications.getExpoPushTokenAsync({
      projectId: projectId,
    });

    // Configure Android channel
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'BizRealms',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4CAF50',
      });
    }

    return tokenResult.data;
  } catch (e) {
    console.log('Error getting push token:', e);
    return null;
  }
}
