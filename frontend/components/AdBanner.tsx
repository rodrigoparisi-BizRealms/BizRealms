import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { AdMobAvailable, AD_UNIT_IDS, BannerAd, BannerAdSize } from '../context/adMobService';

// Simulated ad messages for web fallback
const AD_MESSAGES = [
  { icon: 'rocket', color: '#FF5722', title: 'BizRealms Premium', sub: 'Desbloqueie vantagens exclusivas!' },
  { icon: 'trophy', color: '#FFD700', title: 'Ranking Semanal', sub: 'Jogue e ganhe prêmios reais!' },
  { icon: 'flash', color: '#FF9800', title: 'Boost de Empresa', sub: 'Assista anúncios e ganhe até 10x!' },
  { icon: 'diamond', color: '#9C27B0', title: 'Imóveis de Luxo', sub: 'Invista e multiplique seu patrimônio!' },
  { icon: 'trending-up', color: '#4CAF50', title: 'Investimentos', sub: 'Criptos e ações com alta rentabilidade!' },
  { icon: 'school', color: '#2196F3', title: 'Cursos & Certificações', sub: 'Aumente seu nível e salário!' },
];

export default function AdBanner() {
  const { colors } = useTheme();
  const [dismissed, setDismissed] = useState(false);
  const [adError, setAdError] = useState(false);

  // For web fallback
  const [adIndex, setAdIndex] = useState(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (AdMobAvailable && !adError) return; // Don't rotate on native if AdMob works
    const interval = setInterval(() => {
      Animated.timing(fadeAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start(() => {
        setAdIndex(prev => (prev + 1) % AD_MESSAGES.length);
        Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }).start();
      });
    }, 8000);
    return () => clearInterval(interval);
  }, [adError]);

  if (dismissed) return null;

  // ===== NATIVE: Real AdMob Banner =====
  if (AdMobAvailable && BannerAd && !adError) {
    return (
      <View style={[s.nativeContainer, { backgroundColor: colors.card, borderBottomColor: colors.border }]}>
        <BannerAd
          unitId={AD_UNIT_IDS.BANNER}
          size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER}
          requestOptions={{ requestNonPersonalizedAdsOnly: true }}
          onAdFailedToLoad={(error: any) => {
            console.log('[AdBanner] Failed to load:', error);
            setAdError(true); // Fallback to simulated
          }}
        />
        <TouchableOpacity onPress={() => setDismissed(true)} style={s.nativeClose} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
          <Ionicons name="close" size={14} color={colors.textMuted} />
        </TouchableOpacity>
      </View>
    );
  }

  // ===== WEB / FALLBACK: Simulated Banner =====
  const ad = AD_MESSAGES[adIndex];

  return (
    <View style={[s.container, { backgroundColor: colors.card, borderBottomColor: colors.border }]}>
      <Animated.View style={[s.content, { opacity: fadeAnim }]}>
        <View style={[s.iconWrap, { backgroundColor: ad.color + '20' }]}>
          <Ionicons name={ad.icon as any} size={18} color={ad.color} />
        </View>
        <View style={s.textWrap}>
          <Text style={[s.title, { color: colors.text }]} numberOfLines={1}>{ad.title}</Text>
          <Text style={[s.sub, { color: colors.textSecondary }]} numberOfLines={1}>{ad.sub}</Text>
        </View>
        <View style={s.adLabel}>
          <Text style={s.adLabelText}>AD</Text>
        </View>
      </Animated.View>
      <TouchableOpacity onPress={() => setDismissed(true)} style={s.closeBtn} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
        <Ionicons name="close" size={14} color={colors.textMuted} />
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  // Native banner
  nativeContainer: {
    alignItems: 'center',
    borderBottomWidth: 1,
    position: 'relative',
  },
  nativeClose: {
    position: 'absolute',
    right: 4,
    top: 4,
    padding: 4,
    zIndex: 10,
  },
  // Simulated banner
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
  },
  content: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textWrap: { flex: 1 },
  title: { fontSize: 13, fontWeight: 'bold' },
  sub: { fontSize: 11, marginTop: 1 },
  adLabel: {
    backgroundColor: '#FF5722',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  adLabelText: { color: '#fff', fontSize: 9, fontWeight: 'bold' },
  closeBtn: {
    padding: 6,
    marginLeft: 4,
  },
});
