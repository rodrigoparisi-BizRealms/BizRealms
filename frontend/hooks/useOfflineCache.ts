import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_PREFIX = 'bizrealms_cache_';
const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export function useOfflineCache<T>(key: string, fetcher: () => Promise<T>, ttl: number = DEFAULT_TTL) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [isStale, setIsStale] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = CACHE_PREFIX + key;

  const loadFromCache = useCallback(async (): Promise<T | null> => {
    try {
      const cached = await AsyncStorage.getItem(cacheKey);
      if (cached) {
        const entry: CacheEntry<T> = JSON.parse(cached);
        const isExpired = Date.now() - entry.timestamp > entry.ttl;
        if (!isExpired) {
          return entry.data;
        }
        // Return stale data but mark as stale
        setIsStale(true);
        return entry.data;
      }
    } catch (e) {
      console.warn('Cache read error:', e);
    }
    return null;
  }, [cacheKey]);

  const saveToCache = useCallback(async (data: T) => {
    try {
      const entry: CacheEntry<T> = { data, timestamp: Date.now(), ttl };
      await AsyncStorage.setItem(cacheKey, JSON.stringify(entry));
    } catch (e) {
      console.warn('Cache write error:', e);
    }
  }, [cacheKey, ttl]);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const freshData = await fetcher();
      setData(freshData);
      setIsStale(false);
      await saveToCache(freshData);
      return freshData;
    } catch (e: any) {
      setError(e.message || 'Failed to fetch');
      // If we have cached data, keep using it
      const cached = await loadFromCache();
      if (cached) {
        setData(cached);
        setIsStale(true);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetcher, saveToCache, loadFromCache]);

  useEffect(() => {
    const init = async () => {
      // First load from cache for instant display
      const cached = await loadFromCache();
      if (cached) {
        setData(cached);
        setLoading(false);
      }
      // Then fetch fresh data in background
      await refresh();
    };
    init();
  }, []);

  return { data, loading, isStale, error, refresh };
}

// Utility to clear all cache
export async function clearAllCache() {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const cacheKeys = keys.filter(k => k.startsWith(CACHE_PREFIX));
    if (cacheKeys.length > 0) {
      await AsyncStorage.multiRemove(cacheKeys);
    }
  } catch (e) {
    console.warn('Clear cache error:', e);
  }
}
