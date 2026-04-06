import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Platform,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import Constants from 'expo-constants';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL
  || process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function PrestigeScreen() {
  const { token, refreshUser } = useAuth();
  const { formatMoney } = useLanguage();
  const { colors } = useTheme();
  const router = useRouter();

  const [status, setStatus] = useState<any>(null);
  const [perks, setPerks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [buying, setBuying] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    if (!token) return;
    const h = { Authorization: `Bearer ${token}` };
    try {
      const [statusRes, perksRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/prestige/status`, { headers: h }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/prestige/perks`, { headers: h }),
      ]);
      setStatus(statusRes.data);
      setPerks(perksRes.data.perks || []);
    } catch (e) {
      console.log('Prestige load error:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleBuyPerk = async (perkId: string) => {
    if (!token) return;
    setBuying(perkId);
    try {
      const res = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/prestige/buy-perk`, {
        perk_id: perkId,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.data?.success) {
        const msg = res.data.message || 'Perk ativado!';
        if (Platform.OS === 'web') {
          window.alert(msg);
        } else {
          Alert.alert('Sucesso', msg);
        }
        await loadData();
      }
    } catch (e: any) {
      const errMsg = e?.response?.data?.detail || 'Erro ao comprar perk';
      if (Platform.OS === 'web') {
        window.alert(errMsg);
      } else {
        Alert.alert('Erro', errMsg);
      }
    } finally {
      setBuying(null);
    }
  };

  const handlePrestigeReset = async () => {
    if (!token || !status) return;

    const confirmMsg = `Deseja resetar o jogo?\n\n` +
      `Patrimônio atual: ${formatMoney(status.current_net_worth)}\n` +
      `Pontos que ganhará: +${status.potential_points}\n\n` +
      `Todos os dados serão zerados, mas seus perks permanecerão.`;

    const doReset = async () => {
      setResetting(true);
      try {
        const res = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/prestige/reset`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.data?.success) {
          const msg = res.data.message || 'Prestígio concluído!';
          if (Platform.OS === 'web') {
            window.alert(msg);
          } else {
            Alert.alert('Prestígio!', msg);
          }
          await refreshUser();
          await loadData();
        }
      } catch (e: any) {
        const errMsg = e?.response?.data?.detail || 'Erro no reset';
        if (Platform.OS === 'web') {
          window.alert(errMsg);
        } else {
          Alert.alert('Erro', errMsg);
        }
      } finally {
        setResetting(false);
      }
    };

    if (Platform.OS === 'web') {
      if (window.confirm(confirmMsg)) {
        doReset();
      }
    } else {
      Alert.alert('Prestígio Reset', confirmMsg, [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Resetar', style: 'destructive', onPress: doReset },
      ]);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#FFD700" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  const tier = status?.tier || { emoji: '⚪', name: 'Novato', color: '#9E9E9E' };
  const nextTier = status?.next_tier;

  // Group perks by category
  const categories: Record<string, any[]> = {};
  perks.forEach(p => {
    const cat = p.category || 'other';
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(p);
  });

  const catLabels: Record<string, { icon: string; label: string }> = {
    money: { icon: 'cash', label: 'Capital' },
    xp: { icon: 'flash', label: 'Experiência' },
    companies: { icon: 'business', label: 'Empresas' },
    defense: { icon: 'shield', label: 'Defesa' },
    events: { icon: 'sparkles', label: 'Eventos' },
    investments: { icon: 'trending-up', label: 'Investimentos' },
    jobs: { icon: 'briefcase', label: 'Empregos' },
    status: { icon: 'diamond', label: 'Status' },
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFD700" />}
      >
        {/* Back button */}
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
          <Text style={styles.backText}>Prestígio</Text>
        </TouchableOpacity>

        {/* Tier Card */}
        <View style={[styles.tierCard, { borderColor: tier.color + '50' }]}>
          <Text style={styles.tierEmoji}>{tier.emoji}</Text>
          <Text style={[styles.tierName, { color: tier.color }]}>{tier.name}</Text>
          <View style={styles.tierStats}>
            <View style={styles.tierStat}>
              <Text style={styles.tierStatValue}>{status?.total_points_earned || 0}</Text>
              <Text style={styles.tierStatLabel}>Total ganho</Text>
            </View>
            <View style={[styles.tierStatDivider, { backgroundColor: tier.color + '30' }]} />
            <View style={styles.tierStat}>
              <Text style={[styles.tierStatValue, { color: '#FFD700' }]}>{status?.available_points || 0}</Text>
              <Text style={styles.tierStatLabel}>Disponível</Text>
            </View>
            <View style={[styles.tierStatDivider, { backgroundColor: tier.color + '30' }]} />
            <View style={styles.tierStat}>
              <Text style={styles.tierStatValue}>{status?.resets_count || 0}</Text>
              <Text style={styles.tierStatLabel}>Resets</Text>
            </View>
          </View>
          {nextTier && (
            <Text style={styles.nextTierText}>
              Próximo: {nextTier.emoji} {nextTier.name} ({nextTier.min_points} pts)
            </Text>
          )}
        </View>

        {/* Prestige Reset Button */}
        <TouchableOpacity
          style={[styles.resetBtn, (status?.potential_points || 0) <= 0 && { opacity: 0.5 }]}
          onPress={handlePrestigeReset}
          disabled={resetting || (status?.potential_points || 0) <= 0}
          activeOpacity={0.7}
        >
          {resetting ? (
            <ActivityIndicator color="#000" />
          ) : (
            <>
              <Ionicons name="refresh-circle" size={22} color="#000" />
              <View>
                <Text style={styles.resetBtnText}>
                  Resetar com Prestígio
                </Text>
                <Text style={styles.resetBtnSub}>
                  {(status?.potential_points || 0) > 0
                    ? `+${status.potential_points} pontos (NW: ${formatMoney(status.current_net_worth)})`
                    : 'Patrimônio mínimo: R$ 10.000'}
                </Text>
              </View>
            </>
          )}
        </TouchableOpacity>

        {/* Perks by Category */}
        {Object.entries(categories).map(([cat, catPerks]) => {
          const info = catLabels[cat] || { icon: 'star', label: cat };
          return (
            <View key={cat} style={styles.perkCategory}>
              <View style={styles.perkCatHeader}>
                <Ionicons name={info.icon as any} size={16} color="#aaa" />
                <Text style={styles.perkCatTitle}>{info.label}</Text>
              </View>
              {catPerks.map(perk => {
                const isBuying = buying === perk.id;
                return (
                  <View key={perk.id} style={[
                    styles.perkCard,
                    perk.owned && styles.perkCardOwned,
                    !perk.available && !perk.owned && styles.perkCardLocked,
                  ]}>
                    <View style={styles.perkHeader}>
                      <Text style={{ fontSize: 20 }}>{perk.emoji}</Text>
                      <View style={{ flex: 1 }}>
                        <Text style={[styles.perkName, perk.owned && { color: '#4CAF50' }]}>
                          {perk.name}
                          {perk.owned ? ' ✓' : ''}
                        </Text>
                        <Text style={styles.perkDesc}>{perk.description}</Text>
                      </View>
                      {perk.owned ? (
                        <View style={styles.perkOwnedBadge}>
                          <Text style={styles.perkOwnedText}>Ativo</Text>
                        </View>
                      ) : perk.available ? (
                        <TouchableOpacity
                          style={styles.perkBuyBtn}
                          onPress={() => handleBuyPerk(perk.id)}
                          disabled={isBuying}
                          activeOpacity={0.7}
                        >
                          {isBuying ? (
                            <ActivityIndicator size="small" color="#000" />
                          ) : (
                            <Text style={styles.perkBuyText}>{perk.cost} pts</Text>
                          )}
                        </TouchableOpacity>
                      ) : (
                        <View style={styles.perkLockedBadge}>
                          <Text style={styles.perkLockedText}>{perk.cost} pts</Text>
                        </View>
                      )}
                    </View>
                    {!perk.tier_unlocked && (
                      <Text style={styles.perkReq}>Requer tier {perk.tier_required}</Text>
                    )}
                    {!perk.prerequisite_met && perk.requires && (
                      <Text style={styles.perkReq}>Requer: {perk.requires}</Text>
                    )}
                  </View>
                );
              })}
            </View>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  scroll: { flex: 1 },
  backBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  backText: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  tierCard: {
    backgroundColor: '#1e1e1e',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1.5,
    marginBottom: 16,
  },
  tierEmoji: { fontSize: 48 },
  tierName: { fontSize: 24, fontWeight: 'bold', marginTop: 4 },
  tierStats: { flexDirection: 'row', alignItems: 'center', marginTop: 16, gap: 16 },
  tierStat: { alignItems: 'center' },
  tierStatValue: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  tierStatLabel: { fontSize: 11, color: '#888', marginTop: 2 },
  tierStatDivider: { width: 1, height: 30 },
  nextTierText: { fontSize: 12, color: '#888', marginTop: 12 },
  resetBtn: {
    backgroundColor: '#FFD700',
    borderRadius: 14,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  resetBtnText: { fontSize: 16, fontWeight: 'bold', color: '#000' },
  resetBtnSub: { fontSize: 12, color: '#333', marginTop: 1 },
  perkCategory: { marginBottom: 16 },
  perkCatHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 },
  perkCatTitle: { fontSize: 14, fontWeight: '700', color: '#aaa', textTransform: 'uppercase', letterSpacing: 0.5 },
  perkCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 14,
    padding: 14,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },
  perkCardOwned: { borderColor: '#4CAF5050' },
  perkCardLocked: { opacity: 0.5 },
  perkHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  perkName: { fontSize: 15, fontWeight: '600', color: '#fff' },
  perkDesc: { fontSize: 12, color: '#888', marginTop: 2 },
  perkOwnedBadge: { backgroundColor: 'rgba(76,175,80,0.2)', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  perkOwnedText: { fontSize: 11, color: '#4CAF50', fontWeight: '700' },
  perkBuyBtn: { backgroundColor: '#FFD700', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, minWidth: 60, alignItems: 'center' },
  perkBuyText: { fontSize: 12, fontWeight: '700', color: '#000' },
  perkLockedBadge: { backgroundColor: '#3a3a3a', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  perkLockedText: { fontSize: 11, color: '#666', fontWeight: '600' },
  perkReq: { fontSize: 10, color: '#F44336', marginTop: 4, marginLeft: 30 },
});
