/**
 * BizRealms - Cache Service
 * Provides AsyncStorage-based caching for offline support.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_PREFIX = '@bizrealms_cache_';
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 min default TTL

interface CachedItem<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export const CacheService = {
  /**
   * Store data in cache with a TTL
   */
  async set<T>(key: string, data: T, ttlMs: number = CACHE_TTL_MS): Promise<void> {
    try {
      const item: CachedItem<T> = { data, timestamp: Date.now(), ttl: ttlMs };
      await AsyncStorage.setItem(CACHE_PREFIX + key, JSON.stringify(item));
    } catch (e) {
      console.log('[Cache] Error saving:', key, e);
    }
  },

  /**
   * Get cached data if still valid (within TTL)
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      const raw = await AsyncStorage.getItem(CACHE_PREFIX + key);
      if (!raw) return null;
      const item: CachedItem<T> = JSON.parse(raw);
      const age = Date.now() - item.timestamp;
      if (age > item.ttl) {
        // Expired - but still return it for offline use
        return item.data;
      }
      return item.data;
    } catch (e) {
      console.log('[Cache] Error reading:', key, e);
      return null;
    }
  },

  /**
   * Check if cache entry is fresh (within TTL)
   */
  async isFresh(key: string): Promise<boolean> {
    try {
      const raw = await AsyncStorage.getItem(CACHE_PREFIX + key);
      if (!raw) return false;
      const item = JSON.parse(raw);
      return (Date.now() - item.timestamp) < item.ttl;
    } catch {
      return false;
    }
  },

  /**
   * Remove a specific cache entry
   */
  async remove(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(CACHE_PREFIX + key);
    } catch (e) {
      console.log('[Cache] Error removing:', key, e);
    }
  },

  /**
   * Clear all BizRealms cache entries
   */
  async clearAll(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(k => k.startsWith(CACHE_PREFIX));
      if (cacheKeys.length > 0) {
        await AsyncStorage.multiRemove(cacheKeys);
      }
    } catch (e) {
      console.log('[Cache] Error clearing all:', e);
    }
  },
};
