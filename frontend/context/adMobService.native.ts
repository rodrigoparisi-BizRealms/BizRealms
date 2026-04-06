/**
 * AdMob service - NATIVE version (iOS/Android)
 * Uses real Google AdMob Rewarded Ads
 */
import { Platform } from 'react-native';
import {
  RewardedAd,
  RewardedAdEventType,
  TestIds,
  MobileAds,
} from 'react-native-google-mobile-ads';

export const AdMobAvailable = true;

const REWARDED_AD_UNIT_ID = Platform.select({
  android: __DEV__
    ? TestIds.REWARDED
    : 'ca-app-pub-4504602138884633/3926119981',
  ios: __DEV__
    ? TestIds.REWARDED
    : 'ca-app-pub-4504602138884633/7580422403',
  default: TestIds.REWARDED,
}) as string;

let rewardedAd: ReturnType<typeof RewardedAd.createForAdRequest> | null = null;
let adLoaded = false;
let listeners: Array<() => void> = [];
let onRewardCallback: (() => void) | null = null;
let onAdClosedCallback: (() => void) | null = null;
let onLoadedCallback: ((loaded: boolean) => void) | null = null;

function loadAd() {
  // Cleanup
  listeners.forEach((unsub) => unsub());
  listeners = [];
  adLoaded = false;

  rewardedAd = RewardedAd.createForAdRequest(REWARDED_AD_UNIT_ID, {
    requestNonPersonalizedAdsOnly: true,
  });

  const loadedUnsub = rewardedAd.addAdEventListener(
    RewardedAdEventType.LOADED,
    () => {
      console.log('[AdMob] Rewarded ad loaded');
      adLoaded = true;
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
    console.log('[AdMob] Ad closed');
    adLoaded = false;
    if (onLoadedCallback) onLoadedCallback(false);
    if (onAdClosedCallback) onAdClosedCallback();
    // Reload after closing
    setTimeout(() => loadAd(), 1000);
  });

  listeners = [loadedUnsub, earnedUnsub, closedUnsub];
  rewardedAd.load();
  console.log('[AdMob] Loading rewarded ad...');
}

export async function initializeAdMob() {
  try {
    await MobileAds().initialize();
    console.log('[AdMob] SDK initialized');
    loadAd();
  } catch (e) {
    console.log('[AdMob] Init error:', e);
  }
}

export function useAdMobRewarded() {
  return {
    isLoaded: adLoaded,
    adMobReady: true,
    showRewarded: async (onReward: () => void): Promise<boolean> => {
      if (!adLoaded || !rewardedAd) return false;
      onRewardCallback = onReward;
      try {
        await rewardedAd.show();
        return true;
      } catch (e) {
        console.log('[AdMob] Show error:', e);
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
