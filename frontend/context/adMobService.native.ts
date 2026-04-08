/**
 * AdMob service - NATIVE version (iOS/Android)
 * Uses real Google AdMob: Banner, Interstitial, and Rewarded Ads
 */
import { Platform } from 'react-native';
import {
  RewardedAd,
  RewardedAdEventType,
  InterstitialAd,
  AdEventType,
  TestIds,
  MobileAds,
  BannerAd,
  BannerAdSize,
} from 'react-native-google-mobile-ads';

export const AdMobAvailable = true;

// Re-export for use in components
export { BannerAd, BannerAdSize, TestIds };

// ============================================================
// Ad Unit IDs - Real IDs for production, Test IDs for dev
// ============================================================
export const AD_UNIT_IDS = {
  BANNER: Platform.select({
    android: __DEV__ ? TestIds.BANNER : 'ca-app-pub-4504602138884633/6773541538',
    ios: __DEV__ ? TestIds.BANNER : 'ca-app-pub-4504602138884633/2207813829',
    default: TestIds.BANNER,
  }) as string,
  INTERSTITIAL: Platform.select({
    android: __DEV__ ? TestIds.INTERSTITIAL : 'ca-app-pub-4504602138884633/2612701606',
    ios: __DEV__ ? TestIds.INTERSTITIAL : 'ca-app-pub-4504602138884633/6334557836',
    default: TestIds.INTERSTITIAL,
  }) as string,
  REWARDED: Platform.select({
    android: __DEV__ ? TestIds.REWARDED : 'ca-app-pub-4504602138884633/6631837667',
    ios: __DEV__ ? TestIds.REWARDED : 'ca-app-pub-4504602138884633/4259262098',
    default: TestIds.REWARDED,
  }) as string,
};

// ============================================================
// Rewarded Ad
// ============================================================
let rewardedAd: ReturnType<typeof RewardedAd.createForAdRequest> | null = null;
let rewardedLoaded = false;
let rewardedListeners: Array<() => void> = [];
let onRewardCallback: (() => void) | null = null;
let onAdClosedCallback: (() => void) | null = null;
let onLoadedCallback: ((loaded: boolean) => void) | null = null;

function loadRewardedAd() {
  rewardedListeners.forEach((unsub) => unsub());
  rewardedListeners = [];
  rewardedLoaded = false;

  rewardedAd = RewardedAd.createForAdRequest(AD_UNIT_IDS.REWARDED, {
    requestNonPersonalizedAdsOnly: true,
  });

  const loadedUnsub = rewardedAd.addAdEventListener(
    RewardedAdEventType.LOADED,
    () => {
      console.log('[AdMob] Rewarded ad loaded');
      rewardedLoaded = true;
      if (onLoadedCallback) onLoadedCallback(true);
    }
  );

  const earnedUnsub = rewardedAd.addAdEventListener(
    RewardedAdEventType.EARNED_REWARD,
    (reward) => {
      console.log('[AdMob] Reward earned:', reward);
      if (onRewardCallback) {
        onRewardCallback();
        onRewardCallback = null;
      }
    }
  );

  const closedUnsub = rewardedAd.addAdEventListener('closed' as any, () => {
    console.log('[AdMob] Rewarded ad closed');
    rewardedLoaded = false;
    if (onLoadedCallback) onLoadedCallback(false);
    if (onAdClosedCallback) onAdClosedCallback();
    setTimeout(() => loadRewardedAd(), 1000);
  });

  rewardedListeners = [loadedUnsub, earnedUnsub, closedUnsub];
  rewardedAd.load();
  console.log('[AdMob] Loading rewarded ad...');
}

// ============================================================
// Interstitial Ad
// ============================================================
let interstitialAd: ReturnType<typeof InterstitialAd.createForAdRequest> | null = null;
let interstitialLoaded = false;
let interstitialListeners: Array<() => void> = [];

function loadInterstitialAd() {
  interstitialListeners.forEach((unsub) => unsub());
  interstitialListeners = [];
  interstitialLoaded = false;

  interstitialAd = InterstitialAd.createForAdRequest(AD_UNIT_IDS.INTERSTITIAL, {
    requestNonPersonalizedAdsOnly: true,
  });

  const loadedUnsub = interstitialAd.addAdEventListener(AdEventType.LOADED, () => {
    console.log('[AdMob] Interstitial ad loaded');
    interstitialLoaded = true;
  });

  const closedUnsub = interstitialAd.addAdEventListener(AdEventType.CLOSED, () => {
    console.log('[AdMob] Interstitial ad closed');
    interstitialLoaded = false;
    setTimeout(() => loadInterstitialAd(), 2000);
  });

  interstitialListeners = [loadedUnsub, closedUnsub];
  interstitialAd.load();
  console.log('[AdMob] Loading interstitial ad...');
}

// ============================================================
// Initialize
// ============================================================
export async function initializeAdMob() {
  try {
    await MobileAds().initialize();
    console.log('[AdMob] SDK initialized');
    loadRewardedAd();
    loadInterstitialAd();
  } catch (e) {
    console.log('[AdMob] Init error:', e);
  }
}

// ============================================================
// Hooks / Exports
// ============================================================
export function useAdMobRewarded() {
  return {
    isLoaded: rewardedLoaded,
    adMobReady: true,
    showRewarded: async (onReward: () => void): Promise<boolean> => {
      if (!rewardedLoaded || !rewardedAd) return false;
      onRewardCallback = onReward;
      try {
        await rewardedAd.show();
        return true;
      } catch (e) {
        console.log('[AdMob] Rewarded show error:', e);
        return false;
      }
    },
    setOnLoadedCallback: (cb: (loaded: boolean) => void) => {
      onLoadedCallback = cb;
    },
    setOnAdClosedCallback: (cb: () => void) => {
      onAdClosedCallback = cb;
    },
  };
}

export async function showInterstitialAd(): Promise<boolean> {
  if (!interstitialLoaded || !interstitialAd) {
    console.log('[AdMob] Interstitial not ready');
    return false;
  }
  try {
    await interstitialAd.show();
    return true;
  } catch (e) {
    console.log('[AdMob] Interstitial show error:', e);
    return false;
  }
}
