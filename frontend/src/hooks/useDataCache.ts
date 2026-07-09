'use client';

import { useRef, useCallback } from 'react';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

export function useDataCache<T>(key: string, cacheDuration: number = 5 * 60 * 1000) { // 默认5分钟
  const cache = useRef<Record<string, CacheEntry<T>>>({});

  const getCachedData = useCallback((): T | null => {
    const entry = cache.current[key];
    if (entry) {
      const now = Date.now();
      if (now - entry.timestamp < cacheDuration) {
        return entry.data;
      }
      // 缓存过期，删除
      delete cache.current[key];
    }
    return null;
  }, [key, cacheDuration]);

  const setCachedData = useCallback((data: T) => {
    cache.current[key] = {
      data,
      timestamp: Date.now(),
    };
  }, [key]);

  const clearCache = useCallback(() => {
    delete cache.current[key];
  }, [key]);

  const clearAllCache = useCallback(() => {
    cache.current = {};
  }, []);

  return {
    getCachedData,
    setCachedData,
    clearCache,
    clearAllCache,
  };
}
