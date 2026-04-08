/**
 * BizRealms - Ad Provider (Google AdMob + Web Fallback)
 * 
 * On NATIVE (iOS/Android): Uses real Google AdMob Rewarded Ads via adMobService.native.ts
 * On WEB: Falls back to simulated ad overlay via adMobService.web.ts
 * 
 * Metro automatically resolves the correct platform file.
 */
import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AdMobAvailable, initializeAdMob, useAdMobRewarded, showInterstitialAd } from './adMobService';

interface AdContextType {
  showAd: (onReward: () => void, adType?: string) => void;
  showInterstitial: () => Promise<boolean>;
  isAdPlaying: boolean;
  isAdLoaded: boolean;
  adMobReady: boolean;
}

const AdContext = createContext<AdContextType>({
  showAd: () => {},
  showInterstitial: async () => false,
  isAdPlaying: false,
  isAdLoaded: false,
  adMobReady: false,
});

const SIMULATED_AD_DURATION = 7;

export function AdProvider({ children }: { children: React.ReactNode }) {
  const [isAdPlaying, setIsAdPlaying] = useState(false);
  const [nativeAdLoaded, setNativeAdLoaded] = useState(false);
  const onRewardRef = useRef<(() => void) | null>(null);

  // Simulated ad state
  const [simVisible, setSimVisible] = useState(false);
  const [countdown, setCountdown] = useState(SIMULATED_AD_DURATION);
  const [adType, setAdType] = useState('');
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const progressAnim = useRef(new Animated.Value(0)).current;

  // AdMob service
  const adMob = useAdMobRewarded();

  // Initialize AdMob on native
  useEffect(() => {
    if (AdMobAvailable) {
      initializeAdMob();
      if (adMob.setOnLoadedCallback) {
        adMob.setOnLoadedCallback((loaded: boolean) => setNativeAdLoaded(loaded));
      }
      if (adMob.setOnAdClosedCallback) {
        adMob.setOnAdClosedCallback(() => setIsAdPlaying(false));
      }
    }
  }, []);

  // ==========================================
  // Show Ad (unified)
  // ==========================================
  const showAd = useCallback(async (onReward: () => void, type: string = 'reward') => {
    onRewardRef.current = onReward;

    // Try native AdMob first
    if (AdMobAvailable && adMob.isLoaded) {
      setIsAdPlaying(true);
      const shown = await adMob.showRewarded(onReward);
      if (shown) {
        console.log('[Ad] Showing real AdMob rewarded ad');
        return;
      }
      setIsAdPlaying(false);
    }

    // Fallback: simulated ad
    console.log('[Ad] Showing simulated ad');
    setAdType(type);
    setCountdown(SIMULATED_AD_DURATION);
    setSimVisible(true);
    setIsAdPlaying(true);
    progressAnim.setValue(0);

    Animated.timing(progressAnim, {
      toValue: 1,
      duration: SIMULATED_AD_DURATION * 1000,
      useNativeDriver: false,
    }).start();

    if (timerRef.current) clearInterval(timerRef.current);
    let remaining = SIMULATED_AD_DURATION;
    timerRef.current = setInterval(() => {
      remaining -= 1;
      setCountdown(remaining);
      if (remaining <= 0) {
        if (timerRef.current) clearInterval(timerRef.current);
      }
    }, 1000);
  }, [adMob.isLoaded, progressAnim]);

  // ==========================================
  // Simulated ad close handler
  // ==========================================
  const handleSimClose = () => {
    if (countdown > 0) return;
    setSimVisible(false);
    setIsAdPlaying(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (onRewardRef.current) {
      onRewardRef.current();
      onRewardRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const adMessages: Record<string, { icon: string; title: string; subtitle: string }> = {
    reward: { icon: 'gift', title: 'Special Reward!', subtitle: 'Watch to receive your reward' },
    offer: { icon: 'pricetag', title: 'New Offers!', subtitle: 'Watch to unlock company offers' },
    better_offer: { icon: 'trending-up', title: 'Better Offer!', subtitle: 'Watch to improve the offer value' },
    double: { icon: 'cash', title: 'Double your Gains!', subtitle: 'Watch to double your daily reward' },
    boost: { icon: 'flash', title: 'Company Boost!', subtitle: 'Watch to increase your earnings multiplier' },
  };

  // Interstitial wrapper
  const showInterstitial = useCallback(async () => {
    if (AdMobAvailable) {
      return await showInterstitialAd();
    }
    return false;
  }, []);

  const msg = adMessages[adType] || adMessages.reward;
  const progressWidth = progressAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] });

  return (
    <AdContext.Provider value={{ showAd, showInterstitial, isAdPlaying, isAdLoaded: nativeAdLoaded || AdMobAvailable, adMobReady: AdMobAvailable }}>
      {children}

      {/* Simulated Ad Modal (web or fallback) */}
      <Modal visible={simVisible} animationType="fade" transparent statusBarTranslucent>
        <View style={s.overlay}>
          <View style={s.adContainer}>
            <View style={s.adHeader}>
              <View style={s.adBadge}>
                <Ionicons name="megaphone" size={12} color="#fff" />
                <Text style={s.adBadgeText}>AD</Text>
              </View>
              {countdown > 0 ? (
                <Text style={s.countdownText}>{countdown}s</Text>
              ) : (
                <TouchableOpacity onPress={handleSimClose} style={s.closeBtn}>
                  <Ionicons name="close-circle" size={28} color="#fff" />
                </TouchableOpacity>
              )}
            </View>

            <View style={s.adContent}>
              <View style={s.iconCircle}>
                <Ionicons name={msg.icon as any} size={48} color="#FFD700" />
              </View>
              <Text style={s.adTitle}>{msg.title}</Text>
              <Text style={s.adSubtitle}>{msg.subtitle}</Text>

              <View style={s.adPlaceholder}>
                <Ionicons name="play-circle" size={40} color="#4CAF50" />
                <Text style={s.placeholderText}>BizRealms</Text>
                <Text style={s.placeholderSubtext}>Ad space</Text>
              </View>
            </View>

            <View style={s.progressContainer}>
              <Animated.View style={[s.progressBar, { width: progressWidth }]} />
            </View>

            {countdown <= 0 && (
              <TouchableOpacity style={s.collectBtn} onPress={handleSimClose}>
                <Ionicons name="checkmark-circle" size={22} color="#fff" />
                <Text style={s.collectText}>Collect Reward</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </Modal>
    </AdContext.Provider>
  );
}

export const useAds = () => useContext(AdContext);

const s = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.92)', justifyContent: 'center', alignItems: 'center', padding: 24 },
  adContainer: { width: '100%', maxWidth: 380, backgroundColor: '#1e1e1e', borderRadius: 20, overflow: 'hidden' },
  adHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  adBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#FF5722', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  adBadgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  countdownText: { color: '#888', fontSize: 16, fontWeight: 'bold' },
  closeBtn: { padding: 2 },
  adContent: { alignItems: 'center', padding: 24, gap: 12 },
  iconCircle: { width: 90, height: 90, borderRadius: 45, backgroundColor: '#2a2a2a', alignItems: 'center', justifyContent: 'center' },
  adTitle: { color: '#fff', fontSize: 22, fontWeight: 'bold', textAlign: 'center' },
  adSubtitle: { color: '#aaa', fontSize: 14, textAlign: 'center' },
  adPlaceholder: { width: '100%', height: 120, backgroundColor: '#2a2a2a', borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginTop: 8, gap: 4 },
  placeholderText: { color: '#4CAF50', fontSize: 16, fontWeight: 'bold' },
  placeholderSubtext: { color: '#666', fontSize: 11 },
  progressContainer: { height: 4, backgroundColor: '#333', width: '100%' },
  progressBar: { height: '100%', backgroundColor: '#4CAF50' },
  collectBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: '#4CAF50', margin: 16, paddingVertical: 14, borderRadius: 12 },
  collectText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
