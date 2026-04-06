/**
 * AdMob service - WEB version (no-op)
 * On web, we don't use real ads - just return nulls
 */

export const AdMobAvailable = false;

export function useAdMobRewarded() {
  return {
    isLoaded: false,
    adMobReady: false,
    showRewarded: async (_onReward: () => void): Promise<boolean> => {
      return false; // Not available on web
    },
  };
}

export async function initializeAdMob() {
  // No-op on web
}
