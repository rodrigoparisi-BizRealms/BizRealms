import { safeFixed } from '../utils/safeFixed';
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  RefreshControl, ActivityIndicator, Alert, Platform, Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { SkeletonList } from '../components/SkeletonLoader';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

const AVATAR_COLORS: Record<string, string> = {
  green: '#4CAF50', blue: '#2196F3', purple: '#9C27B0',
  orange: '#FF9800', red: '#F44336', yellow: '#FFC107',
};

const formatMoney = (v: number) => {
  if (v >= 1_000_000) return `$ ${safeFixed(v / 1_000_000, 1)}M`;
  if (v >= 1_000) return `$ ${safeFixed(v / 1_000, 1)}K`;
  return `$ ${v.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

const showAlert = (title: string, msg: string) => {
  if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
  else Alert.alert(title, msg);
};

export default function Rankings() {
  const { token, user, refreshUser } = useAuth();
  const { t, formatMoney: fmtCurrency } = useLanguage();
  const router = useRouter();
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [distributing, setDistributing] = useState(false);
  const [showRewardModal, setShowRewardModal] = useState(false);
  const [prizePool, setPrizePool] = useState<any>(null);
  const [claimingReal, setClaimingReal] = useState(false);

  const loadRankings = useCallback(async () => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [r, pp] = await Promise.all([
        axios.get(`${API}/api/rankings?period=${period}`, { headers: h }),
        axios.get(`${API}/api/rewards/prize-pool`, { headers: h }).catch(() => ({ data: null })),
      ]);
      setData(r.data);
      setPrizePool(pp.data);
    } catch (e) { console.error('Rankings error:', e); }
    finally { setLoading(false); }
  }, [token, period]);

  useEffect(() => { setLoading(true); loadRankings(); }, [loadRankings]);

  const onRefresh = async () => { setRefreshing(true); await loadRankings(); setRefreshing(false); };

  // Auto-show reward modal if unclaimed
  useEffect(() => {
    if (data?.has_unclaimed_reward) {
      setShowRewardModal(true);
    }
  }, [data?.has_unclaimed_reward]);

  const handleDistribute = async () => {
    setDistributing(true);
    try {
      const r = await axios.post(`${API}/api/rankings/distribute-rewards`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      showAlert(
        r.data.distributed ? 'Prêmios Distribuídos!' : 'Aguarde',
        r.data.message
      );
      if (r.data.distributed) await loadRankings();
    } catch (e: any) {
      showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setDistributing(false); }
  };

  const handleClaim = async () => {
    setClaiming(true);
    try {
      const r = await axios.post(`${API}/api/rankings/claim-reward`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      showAlert('Prêmio Resgatado!', r.data.message);
      setShowRewardModal(false);
      await refreshUser();
      await loadRankings();
    } catch (e: any) {
      showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setClaiming(false); }
  };

  const handleClaimRealMoney = async (rewardId: string) => {
    setClaimingReal(true);
    try {
      const r = await axios.post(`${API}/api/rewards/claim-real`, { reward_id: rewardId }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      showAlert('Resgate Solicitado!', r.data.message);
      await loadRankings();
    } catch (e: any) {
      showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setClaimingReal(false); }
  };

  const handleDistributeReal = async () => {
    try {
      const r = await axios.post(`${API}/api/rewards/distribute-monthly`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      showAlert(r.data.success ? 'Distribuído!' : 'Info', r.data.message);
      if (r.data.success) await loadRankings();
    } catch (e: any) {
      showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
    }
  };

  const currentUser = data?.current_user;
  const prizes = data?.prizes || [];

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}>
        <ActivityIndicator size="large" color="#FFD700" />
        <Text style={s.loadText}>{t('general.loading')}</Text>
      </View>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity style={s.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>{t('rankings.title')}</Text>
          <Text style={s.subtitle}>{data?.total_players || 0} jogadores</Text>
        </View>
        <Ionicons name="trophy" size={28} color="#FFD700" />
      </View>

      {/* Period Toggle */}
      <View style={s.toggleRow}>
        <TouchableOpacity
          style={[s.toggleBtn, period === 'weekly' && s.toggleActive]}
          onPress={() => setPeriod('weekly')}
        >
          <Ionicons name="calendar" size={16} color={period === 'weekly' ? '#fff' : '#888'} />
          <Text style={[s.toggleText, period === 'weekly' && s.toggleTextActive]}>{t('rankings.weekly')}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[s.toggleBtn, period === 'monthly' && s.toggleActive]}
          onPress={() => setPeriod('monthly')}
        >
          <Ionicons name="calendar" size={16} color={period === 'monthly' ? '#fff' : '#888'} />
          <Text style={[s.toggleText, period === 'monthly' && s.toggleTextActive]}>{t('rankings.monthly')}</Text>
        </TouchableOpacity>
      </View>

      {/* Weekly Prizes Banner */}
      {period === 'weekly' && prizes.length > 0 && (
        <View style={s.prizesBanner}>
          <Text style={s.prizesTitle}>{t('rankings.prizes')}</Text>
          <View style={s.prizesRow}>
            {prizes.map((p: any) => (
              <View key={p.position} style={s.prizeItem}>
                <View style={[s.prizeIcon, { backgroundColor: `${p.color}30` }]}>
                  <Ionicons name={(p.icon || 'gift') as any} size={18} color={p.color} />
                </View>
                <Text style={[s.prizePos, { color: p.color }]}>
                  {p.position === 1 ? '1º' : p.position === 2 ? '2º' : '3º'}
                </Text>
                <Text style={s.prizeDesc} numberOfLines={2}>{p.description}</Text>
              </View>
            ))}
          </View>
          <TouchableOpacity
            style={[s.distributeBtn, distributing && { opacity: 0.5 }]}
            onPress={handleDistribute}
            disabled={distributing}
          >
            {distributing ? (
              <ActivityIndicator size="small" color="#FFD700" />
            ) : (
              <>
                <Ionicons name="gift" size={16} color="#FFD700" />
                <Text style={s.distributeBtnText}>{t('rankings.distribution')}</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Current User Position */}
      {currentUser && (
        <View style={s.myRankCard}>
          <View style={s.myRankLeft}>
            <Text style={s.myRankPos}>#{currentUser.position}</Text>
            <View style={[s.avatar, { backgroundColor: AVATAR_COLORS[currentUser.avatar_color] || '#4CAF50' }]}>
              <Ionicons name={(currentUser.avatar_icon || 'person') as any} size={20} color="#fff" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.myRankName}>{t('rankings.you')}</Text>
              <Text style={s.myRankLevel}>{t('profile.levelLabel')} {currentUser.level}</Text>
            </View>
          </View>
          <View style={s.myRankRight}>
            <Text style={s.myRankValue}>{formatMoney(currentUser.total_net_worth)}</Text>
            {currentUser.position_change !== 0 && (
              <View style={s.changeRow}>
                <Ionicons
                  name={currentUser.position_change > 0 ? 'arrow-up' : 'arrow-down'}
                  size={12}
                  color={currentUser.position_change > 0 ? '#4CAF50' : '#F44336'}
                />
                <Text style={{ color: currentUser.position_change > 0 ? '#4CAF50' : '#F44336', fontSize: 11, fontWeight: 'bold' }}>
                  {Math.abs(currentUser.position_change)}
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Top 3 Podium */}
      {data?.rankings?.length >= 3 && (
        <View style={s.podium}>
          {/* 2nd place */}
          <View style={s.podiumItem}>
            <View style={[s.podiumAvatar, { backgroundColor: AVATAR_COLORS[data.rankings[1].avatar_color] || '#2196F3', borderColor: '#C0C0C0' }]}>
              <Ionicons name={(data.rankings[1].avatar_icon || 'person') as any} size={20} color="#fff" />
            </View>
            <View style={[s.podiumBar, { height: 50, backgroundColor: '#C0C0C0' }]}>
              <Text style={s.podiumPosNum}>2</Text>
            </View>
            <Text style={s.podiumName} numberOfLines={1}>{data.rankings[1].name}</Text>
            <Text style={s.podiumVal}>{formatMoney(data.rankings[1].total_net_worth)}</Text>
            <Text style={[s.podiumPrize, { color: '#C0C0C0' }]}>5x 24h</Text>
          </View>
          {/* 1st place */}
          <View style={s.podiumItem}>
            <Ionicons name="star" size={22} color="#FFD700" style={{ marginBottom: 4 }} />
            <View style={[s.podiumAvatar, s.podiumAvatarFirst, { backgroundColor: AVATAR_COLORS[data.rankings[0].avatar_color] || '#4CAF50', borderColor: '#FFD700' }]}>
              <Ionicons name={(data.rankings[0].avatar_icon || 'person') as any} size={24} color="#fff" />
            </View>
            <View style={[s.podiumBar, { height: 70, backgroundColor: '#FFD700' }]}>
              <Text style={[s.podiumPosNum, { color: '#000' }]}>1</Text>
            </View>
            <Text style={[s.podiumName, { color: '#FFD700' }]} numberOfLines={1}>{data.rankings[0].name}</Text>
            <Text style={[s.podiumVal, { color: '#FFD700' }]}>{formatMoney(data.rankings[0].total_net_worth)}</Text>
            <Text style={[s.podiumPrize, { color: '#FFD700' }]}>+50K XP</Text>
          </View>
          {/* 3rd place */}
          <View style={s.podiumItem}>
            <View style={[s.podiumAvatar, { backgroundColor: AVATAR_COLORS[data.rankings[2].avatar_color] || '#FF9800', borderColor: '#CD7F32' }]}>
              <Ionicons name={(data.rankings[2].avatar_icon || 'person') as any} size={20} color="#fff" />
            </View>
            <View style={[s.podiumBar, { height: 35, backgroundColor: '#CD7F32' }]}>
              <Text style={s.podiumPosNum}>3</Text>
            </View>
            <Text style={s.podiumName} numberOfLines={1}>{data.rankings[2].name}</Text>
            <Text style={s.podiumVal}>{formatMoney(data.rankings[2].total_net_worth)}</Text>
            <Text style={[s.podiumPrize, { color: '#CD7F32' }]}>+$25K</Text>
          </View>
        </View>
      )}

      {/* Full Rankings List */}
      <ScrollView
        contentContainerStyle={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFD700" />}
      >
        {(data?.rankings || []).slice(3).map((r: any) => {
          const isMe = r.user_id === user?.id;
          return (
            <TouchableOpacity key={r.user_id} style={[s.rankRow, isMe && s.rankRowMe]} onPress={() => !isMe && router.push(`/player-profile?id=${r.user_id}`)}>
              <Text style={[s.rankPos, isMe && { color: '#FFD700' }]}>#{r.position}</Text>
              <View style={[s.rankAvatar, { backgroundColor: AVATAR_COLORS[r.avatar_color] || '#4CAF50' }]}>
                <Ionicons name={(r.avatar_icon || 'person') as any} size={16} color="#fff" />
              </View>
              <View style={s.rankInfo}>
                <Text style={[s.rankName, isMe && { color: '#FFD700' }]} numberOfLines={1}>
                  {isMe ? 'Você' : r.name}
                </Text>
                <Text style={s.rankMeta}>Nv {r.level} • {r.num_companies} emp. • {r.num_assets} bens</Text>
              </View>
              <View style={s.rankRight}>
                <Text style={s.rankValue}>{formatMoney(r.total_net_worth)}</Text>
                {r.cert_count > 0 && (
                  <Text style={{ fontSize: 10, color: '#FF9800', fontWeight: 'bold' }}>🎓+{r.cert_bonus_pct}%</Text>
                )}
                {r.position_change !== 0 && !r.is_new && (
                  <View style={s.changeRow}>
                    <Ionicons
                      name={r.position_change > 0 ? 'arrow-up' : 'arrow-down'}
                      size={10}
                      color={r.position_change > 0 ? '#4CAF50' : '#F44336'}
                    />
                    <Text style={{ color: r.position_change > 0 ? '#4CAF50' : '#F44336', fontSize: 10, fontWeight: 'bold' }}>
                      {Math.abs(r.position_change)}
                    </Text>
                  </View>
                )}
                {r.is_new && (
                  <Text style={s.newBadge}>NOVO</Text>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {(!data?.rankings || data.rankings.length === 0) && (
          <View style={s.empty}>
            <Ionicons name="trophy-outline" size={48} color="#555" />
            <Text style={s.emptyText}>{t('rankings.noRankings')}</Text>
          </View>
        )}
      </ScrollView>

      {/* Real Money Prize Pool Section */}
      {prizePool && (
        <View style={s.realPrizeSection}>
          <View style={s.realPrizeHeader}>
            <Ionicons name="cash" size={22} color="#FFD700" />
            <Text style={s.realPrizeTitle}>{t('rankings.realPrize')}</Text>
          </View>
          <View style={s.realPrizePool}>
            <Text style={s.realPrizeLabel}>{t('rankings.monthPool')}</Text>
            <Text style={s.realPrizeAmount}>$ {safeFixed(prizePool.prize_pool_total, 2)}</Text>
            <Text style={s.realPrizeSub}>5% da receita de ads • {prizePool.days_remaining || 0} dias restantes</Text>
          </View>
          <View style={s.realDistRow}>
            <View style={[s.realDistItem, { borderColor: '#FFD700' }]}>
              <Text style={[s.realDistPos, { color: '#FFD700' }]}>1º</Text>
              <Text style={s.realDistAmount}>$ {safeFixed(prizePool.distribution?.['1st'], 2)}</Text>
              <Text style={s.realDistPct}>60%</Text>
            </View>
            <View style={[s.realDistItem, { borderColor: '#C0C0C0' }]}>
              <Text style={[s.realDistPos, { color: '#C0C0C0' }]}>2º</Text>
              <Text style={s.realDistAmount}>$ {safeFixed(prizePool.distribution?.['2nd'], 2)}</Text>
              <Text style={s.realDistPct}>30%</Text>
            </View>
            <View style={[s.realDistItem, { borderColor: '#CD7F32' }]}>
              <Text style={[s.realDistPos, { color: '#CD7F32' }]}>3º</Text>
              <Text style={s.realDistAmount}>$ {safeFixed(prizePool.distribution?.['3rd'], 2)}</Text>
              <Text style={s.realDistPct}>10%</Text>
            </View>
          </View>
          {!prizePool.has_paypal && (
            <View style={s.pixWarning}>
              <Ionicons name="warning" size={16} color="#FF9800" />
              <Text style={s.pixWarningText}>{t('rankings.configPaypal')}</Text>
            </View>
          )}
          {prizePool.has_unclaimed_reward && prizePool.unclaimed_reward && (
            <TouchableOpacity
              style={[s.claimRealBtn, claimingReal && { opacity: 0.5 }]}
              onPress={() => handleClaimRealMoney(prizePool.unclaimed_reward.id)}
              disabled={claimingReal}
            >
              <Ionicons name="gift" size={20} color="#000" />
              <Text style={s.claimRealText}>
                Resgatar $ {safeFixed(prizePool.unclaimed_reward.amount, 2)} ({prizePool.unclaimed_reward.position}º lugar)
              </Text>
            </TouchableOpacity>
          )}
          <Text style={s.realPrizeYou}>
            Sua posição: #{prizePool.user_position || '?'} de {prizePool.total_players || 0} jogadores
          </Text>
        </View>
      )}

      {/* Reward Claim Modal */}
      <Modal visible={showRewardModal} animationType="slide" transparent onRequestClose={() => setShowRewardModal(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>{t('rankings.reward')}</Text>
              <TouchableOpacity onPress={() => setShowRewardModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            {data?.unclaimed_reward && (
              <View style={s.rewardContent}>
                {/* Trophy animation area */}
                <View style={s.rewardTrophy}>
                  <View style={[s.trophyCircle, {
                    backgroundColor: data.unclaimed_reward.position === 1 ? '#FFD70030'
                      : data.unclaimed_reward.position === 2 ? '#C0C0C030'
                      : '#CD7F3230'
                  }]}>
                    <Ionicons
                      name="trophy"
                      size={64}
                      color={data.unclaimed_reward.position === 1 ? '#FFD700'
                        : data.unclaimed_reward.position === 2 ? '#C0C0C0'
                        : '#CD7F32'}
                    />
                  </View>
                </View>

                <Text style={s.rewardPosition}>
                  {data.unclaimed_reward.position === 1 ? '1º Lugar!' :
                   data.unclaimed_reward.position === 2 ? '2º Lugar!' : '3º Lugar!'}
                </Text>
                <Text style={s.rewardWeek}>Semana {data.unclaimed_reward.week_of}</Text>
                <Text style={s.rewardDesc}>{data.unclaimed_reward.reward_description}</Text>

                <TouchableOpacity
                  style={[s.claimBtn, claiming && { opacity: 0.5 }]}
                  onPress={handleClaim}
                  disabled={claiming}
                >
                  {claiming ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <>
                      <Ionicons name="gift" size={20} color="#fff" />
                      <Text style={s.claimBtnText}>{t('rankings.claimReward')}</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadText: { color: '#888', fontSize: 16 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  backBtn: { width: 40, height: 40, borderRadius: 12, backgroundColor: '#2a2a2a', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { color: '#888', fontSize: 12 },
  // Toggle
  toggleRow: { flexDirection: 'row', marginHorizontal: 16, backgroundColor: '#2a2a2a', borderRadius: 12, padding: 4, marginBottom: 12 },
  toggleBtn: { flex: 1, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, paddingVertical: 10, borderRadius: 10 },
  toggleActive: { backgroundColor: '#3a3a3a' },
  toggleText: { color: '#888', fontSize: 14, fontWeight: 'bold' },
  toggleTextActive: { color: '#fff' },
  // Prizes Banner
  prizesBanner: { marginHorizontal: 16, backgroundColor: '#1a1a2a', borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: '#FFD70040' },
  prizesTitle: { color: '#FFD700', fontSize: 16, fontWeight: 'bold', textAlign: 'center', marginBottom: 12 },
  prizesRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  prizeItem: { alignItems: 'center', flex: 1 },
  prizeIcon: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center', marginBottom: 6 },
  prizePos: { fontSize: 14, fontWeight: 'bold' },
  prizeDesc: { color: '#aaa', fontSize: 10, textAlign: 'center', marginTop: 2 },
  distributeBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 10, borderRadius: 10, backgroundColor: '#2a2a2a', borderWidth: 1, borderColor: '#FFD70040' },
  distributeBtnText: { color: '#FFD700', fontSize: 13, fontWeight: 'bold' },
  // My Rank
  myRankCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginHorizontal: 16, backgroundColor: '#2a2a2a', borderRadius: 14, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: '#FFD700' },
  myRankLeft: { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 },
  myRankPos: { color: '#FFD700', fontSize: 18, fontWeight: 'bold', width: 40 },
  myRankName: { color: '#FFD700', fontSize: 15, fontWeight: 'bold' },
  myRankLevel: { color: '#888', fontSize: 12 },
  myRankRight: { alignItems: 'flex-end' },
  myRankValue: { color: '#FFD700', fontSize: 16, fontWeight: 'bold' },
  avatar: { width: 34, height: 34, borderRadius: 17, justifyContent: 'center', alignItems: 'center' },
  // Podium
  podium: { flexDirection: 'row', justifyContent: 'center', alignItems: 'flex-end', paddingHorizontal: 16, paddingBottom: 12, gap: 8 },
  podiumItem: { alignItems: 'center', flex: 1 },
  podiumAvatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center', borderWidth: 2, marginBottom: 4 },
  podiumAvatarFirst: { width: 48, height: 48, borderRadius: 24, borderWidth: 3 },
  podiumBar: { width: '80%', borderTopLeftRadius: 8, borderTopRightRadius: 8, justifyContent: 'center', alignItems: 'center' },
  podiumPosNum: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  podiumName: { color: '#ccc', fontSize: 11, fontWeight: 'bold', marginTop: 4, textAlign: 'center' },
  podiumVal: { color: '#888', fontSize: 10, marginTop: 2 },
  podiumPrize: { fontSize: 9, fontWeight: 'bold', marginTop: 2 },
  // List
  list: { paddingHorizontal: 16, paddingBottom: 32 },
  rankRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#2a2a2a', borderRadius: 12, padding: 12, marginBottom: 8, gap: 10 },
  rankRowMe: { borderWidth: 1, borderColor: '#FFD70050' },
  rankPos: { color: '#888', fontSize: 14, fontWeight: 'bold', width: 36 },
  rankAvatar: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  rankInfo: { flex: 1 },
  rankName: { color: '#fff', fontSize: 14, fontWeight: '600' },
  rankMeta: { color: '#666', fontSize: 11, marginTop: 2 },
  rankRight: { alignItems: 'flex-end' },
  rankValue: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  changeRow: { flexDirection: 'row', alignItems: 'center', gap: 2, marginTop: 2 },
  newBadge: { color: '#4CAF50', fontSize: 9, fontWeight: 'bold', marginTop: 2 },
  empty: { alignItems: 'center', paddingVertical: 40 },
  emptyText: { color: '#666', fontSize: 16, marginTop: 12 },
  // Reward Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'center' },
  modal: { backgroundColor: '#1a1a1a', borderRadius: 24, marginHorizontal: 24, padding: 24, maxHeight: '80%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modalTitle: { fontSize: 22, fontWeight: 'bold', color: '#FFD700' },
  rewardContent: { alignItems: 'center' },
  rewardTrophy: { marginBottom: 16 },
  trophyCircle: { width: 120, height: 120, borderRadius: 60, justifyContent: 'center', alignItems: 'center' },
  rewardPosition: { color: '#fff', fontSize: 28, fontWeight: 'bold', marginBottom: 4 },
  rewardWeek: { color: '#888', fontSize: 13, marginBottom: 16 },
  rewardDesc: { color: '#4CAF50', fontSize: 18, fontWeight: 'bold', textAlign: 'center', marginBottom: 24 },
  claimBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: '#FFD700', borderRadius: 14, paddingVertical: 16, paddingHorizontal: 32, width: '100%' },
  claimBtnText: { color: '#000', fontSize: 18, fontWeight: 'bold' },
  // Real Prize Section
  realPrizeSection: { marginHorizontal: 16, backgroundColor: '#1a1a2a', borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#FFD70050' },
  realPrizeHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  realPrizeTitle: { color: '#FFD700', fontSize: 18, fontWeight: 'bold' },
  realPrizePool: { alignItems: 'center', marginBottom: 14, paddingVertical: 10, backgroundColor: '#FFD70010', borderRadius: 12 },
  realPrizeLabel: { color: '#888', fontSize: 12 },
  realPrizeAmount: { color: '#FFD700', fontSize: 28, fontWeight: 'bold', marginTop: 4 },
  realPrizeSub: { color: '#666', fontSize: 11, marginTop: 4 },
  realDistRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  realDistItem: { flex: 1, alignItems: 'center', backgroundColor: '#2a2a3a', borderRadius: 10, padding: 10, borderWidth: 1 },
  realDistPos: { fontSize: 16, fontWeight: 'bold' },
  realDistAmount: { color: '#fff', fontSize: 13, fontWeight: 'bold', marginTop: 4 },
  realDistPct: { color: '#666', fontSize: 10, marginTop: 2 },
  pixWarning: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#FF980020', borderRadius: 10, padding: 10, marginBottom: 10 },
  pixWarningText: { color: '#FF9800', fontSize: 12, flex: 1 },
  claimRealBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: '#FFD700', borderRadius: 12, paddingVertical: 14, marginBottom: 10 },
  claimRealText: { color: '#000', fontSize: 15, fontWeight: 'bold' },
  realPrizeYou: { color: '#888', fontSize: 12, textAlign: 'center' },
});
