/**
 * BizRealms - Network Context
 * Provides network status detection and offline indicator.
 */
import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import * as Network from 'expo-network';
import { View, Text, StyleSheet, Animated, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface NetworkContextType {
  isConnected: boolean;
  isOffline: boolean;
  checkConnection: () => Promise<boolean>;
}

const NetworkContext = createContext<NetworkContextType>({
  isConnected: true,
  isOffline: false,
  checkConnection: async () => true,
});

export function NetworkProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(true);
  const slideAnim = useRef(new Animated.Value(-40)).current;

  const checkConnection = useCallback(async (): Promise<boolean> => {
    try {
      const state = await Network.getNetworkStateAsync();
      const connected = state.isConnected === true && state.isInternetReachable !== false;
      setIsConnected(connected);
      return connected;
    } catch {
      return true; // Assume connected if check fails
    }
  }, []);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 15000); // Check every 15 sec
    return () => clearInterval(interval);
  }, [checkConnection]);

  // Animate offline banner
  useEffect(() => {
    Animated.timing(slideAnim, {
      toValue: isConnected ? -40 : 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [isConnected, slideAnim]);

  return (
    <NetworkContext.Provider value={{ isConnected, isOffline: !isConnected, checkConnection }}>
      {children}
      <Animated.View style={[styles.offlineBanner, { transform: [{ translateY: slideAnim }] }]}>
        <Ionicons name="cloud-offline" size={16} color="#fff" />
        <Text style={styles.offlineText}>Modo Offline - Dados em cache</Text>
      </Animated.View>
    </NetworkContext.Provider>
  );
}

export const useNetwork = () => useContext(NetworkContext);

const styles = StyleSheet.create({
  offlineBanner: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 36,
    backgroundColor: '#FF5722',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    zIndex: 9999,
    ...Platform.select({
      ios: { paddingTop: 0 },
      android: { paddingTop: 0 },
      web: { paddingTop: 0 },
    }),
  },
  offlineText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
});
