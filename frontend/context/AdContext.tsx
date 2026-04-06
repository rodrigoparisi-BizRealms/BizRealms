/**
 * BizRealms - Ad Provider (Simulated)
 * Shows a simulated ad (countdown modal) that can be replaced with real AdMob later.
 * When AdMob keys are available, replace showAd() internals with real rewarded ad calls.
 */
import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, Animated, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface AdContextType {
  showAd: (onReward: () => void, adType?: string) => void;
  isAdPlaying: boolean;
}

const AdContext = createContext<AdContextType>({
  showAd: () => {},
  isAdPlaying: false,
});

const AD_DURATION = 7; // seconds (simulated)

export function AdProvider({ children }: { children: React.ReactNode }) {
  const [visible, setVisible] = useState(false);
  const [countdown, setCountdown] = useState(AD_DURATION);
  const [adType, setAdType] = useState('');
  const onRewardRef = useRef<(() => void) | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const progressAnim = useRef(new Animated.Value(0)).current;

  const showAd = useCallback((onReward: () => void, type: string = 'reward') => {
    onRewardRef.current = onReward;
    setAdType(type);
    setCountdown(AD_DURATION);
    setVisible(true);
    progressAnim.setValue(0);

    Animated.timing(progressAnim, {
      toValue: 1,
      duration: AD_DURATION * 1000,
      useNativeDriver: false,
    }).start();

    if (timerRef.current) clearInterval(timerRef.current);
    let remaining = AD_DURATION;
    timerRef.current = setInterval(() => {
      remaining -= 1;
      setCountdown(remaining);
      if (remaining <= 0) {
        if (timerRef.current) clearInterval(timerRef.current);
      }
    }, 1000);
  }, [progressAnim]);

  const handleClose = () => {
    if (countdown > 0) return; // Can't close yet
    setVisible(false);
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
    reward: { icon: 'gift', title: 'Recompensa Especial!', subtitle: 'Assista para receber sua recompensa' },
    offer: { icon: 'pricetag', title: 'Novas Ofertas!', subtitle: 'Assista para desbloquear ofertas de empresas' },
    better_offer: { icon: 'trending-up', title: 'Melhor Oferta!', subtitle: 'Assista para melhorar o valor da oferta' },
    double: { icon: 'cash', title: 'Duplique seus Ganhos!', subtitle: 'Assista para dobrar sua recompensa diária' },
  };

  const msg = adMessages[adType] || adMessages.reward;

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  return (
    <AdContext.Provider value={{ showAd, isAdPlaying: visible }}>
      {children}
      <Modal visible={visible} animationType="fade" transparent statusBarTranslucent>
        <View style={s.overlay}>
          <View style={s.adContainer}>
            {/* Ad simulation header */}
            <View style={s.adHeader}>
              <View style={s.adBadge}>
                <Ionicons name="megaphone" size={12} color="#fff" />
                <Text style={s.adBadgeText}>AD</Text>
              </View>
              {countdown > 0 ? (
                <Text style={s.countdownText}>{countdown}s</Text>
              ) : (
                <TouchableOpacity onPress={handleClose} style={s.closeBtn}>
                  <Ionicons name="close-circle" size={28} color="#fff" />
                </TouchableOpacity>
              )}
            </View>

            {/* Ad content (simulated) */}
            <View style={s.adContent}>
              <View style={s.iconCircle}>
                <Ionicons name={msg.icon as any} size={48} color="#FFD700" />
              </View>
              <Text style={s.adTitle}>{msg.title}</Text>
              <Text style={s.adSubtitle}>{msg.subtitle}</Text>

              {/* Simulated ad placeholder */}
              <View style={s.adPlaceholder}>
                <Ionicons name="play-circle" size={40} color="#4CAF50" />
                <Text style={s.placeholderText}>BizRealms Premium</Text>
                <Text style={s.placeholderSubtext}>Espaço reservado para anúncio</Text>
              </View>
            </View>

            {/* Progress bar */}
            <View style={s.progressContainer}>
              <Animated.View style={[s.progressBar, { width: progressWidth }]} />
            </View>

            {/* Collect button (only after countdown) */}
            {countdown <= 0 && (
              <TouchableOpacity style={s.collectBtn} onPress={handleClose}>
                <Ionicons name="checkmark-circle" size={22} color="#fff" />
                <Text style={s.collectText}>Coletar Recompensa</Text>
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
