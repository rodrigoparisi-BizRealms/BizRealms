/**
 * AdMob service - WEB version (fallback/mock)
 * Web does not support Google AdMob - all ads are simulated
 */

export const AdMobAvailable = false;

// Mock exports for web compatibility
export const AD_UNIT_IDS = {
  BANNER: 'web-mock-banner',
  INTERSTITIAL: 'web-mock-interstitial',
  REWARDED: 'web-mock-rewarded',
};

export function useAdMobRewarded() {
  return {
    isLoaded: false,
    adMobReady: false,
    showRewarded: async (_onReward: () => void): Promise<boolean> => false,
    setOnLoadedCallback: (_cb: (loaded: boolean) => void) => {},
    setOnAdClosedCallback: (_cb: () => void) => {},
  };
}

export async function showInterstitialAd(): Promise<boolean> {
  console.log('[AdMob Web] Interstitial not available on web');
  return false;
}

export async function initializeAdMob() {
  console.log('[AdMob Web] No-op on web');
}

// Mock BannerAd and BannerAdSize for web (will not render)
export const BannerAd = null;
export const BannerAdSize = {
  BANNER: 'BANNER',
  FULL_BANNER: 'FULL_BANNER',
  ANCHORED_ADAPTIVE_BANNER: 'ANCHORED_ADAPTIVE_BANNER',
};
export const TestIds = {
  BANNER: 'test-banner',
  INTERSTITIAL: 'test-interstitial',
  REWARDED: 'test-rewarded',
};
