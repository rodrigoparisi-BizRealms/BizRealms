import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  RefreshControl, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'expo-router';
import axios from 'axios';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

const MEDALS = ['', '#FFD700', '#C0C0C0', '#CD7F32']; // gold, silver, bronze
const AVATAR_COLORS: Record<string, string> = {
  green: '#4CAF50', blue: '#2196F3', purple: '#9C27B0',
  orange: '#FF9800', red: '#F44336', yellow: '#FFC107',
};

const formatMoney = (v: number) => {
  if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(1)}K`;
  return `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

export default function Rankings() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadRankings = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/api/rankings?period=${period}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(r.data);
    } catch (e) { console.error('Rankings error:', e); }
    finally { setLoading(false); }
  }, [token, period]);

  useEffect(() => { setLoading(true); loadRankings(); }, [loadRankings]);

  const onRefresh = async () => { setRefreshing(true); await loadRankings(); setRefreshing(false); };

  const currentUser = data?.current_user;

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}>
        <ActivityIndicator size="large" color="#FFD700" />
        <Text style={s.loadText}>Carregando rankings...</Text>
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
          <Text style={s.title}>Rankings</Text>
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
          <Text style={[s.toggleText, period === 'weekly' && s.toggleTextActive]}>Semanal</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[s.toggleBtn, period === 'monthly' && s.toggleActive]}
          onPress={() => setPeriod('monthly')}
        >
          <Ionicons name="calendar" size={16} color={period === 'monthly' ? '#fff' : '#888'} />
          <Text style={[s.toggleText, period === 'monthly' && s.toggleTextActive]}>Mensal</Text>
        </TouchableOpacity>
      </View>

      {/* Current User Position */}
      {currentUser && (
        <View style={s.myRankCard}>
          <View style={s.myRankLeft}>
            <Text style={s.myRankPos}>#{currentUser.position}</Text>
            <View style={[s.avatar, { backgroundColor: AVATAR_COLORS[currentUser.avatar_color] || '#4CAF50' }]}>
              <Ionicons name={(currentUser.avatar_icon || 'person') as any} size={20} color="#fff" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.myRankName}>Você</Text>
              <Text style={s.myRankLevel}>Nível {currentUser.level}</Text>
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
              <Text style={s.podiumPos}>2</Text>
            </View>
            <Text style={s.podiumName} numberOfLines={1}>{data.rankings[1].name}</Text>
            <Text style={s.podiumVal}>{formatMoney(data.rankings[1].total_net_worth)}</Text>
          </View>
          {/* 1st place */}
          <View style={s.podiumItem}>
            <Ionicons name="star" size={22} color="#FFD700" style={{ marginBottom: 4 }} />
            <View style={[s.podiumAvatar, s.podiumAvatarFirst, { backgroundColor: AVATAR_COLORS[data.rankings[0].avatar_color] || '#4CAF50', borderColor: '#FFD700' }]}>
              <Ionicons name={(data.rankings[0].avatar_icon || 'person') as any} size={24} color="#fff" />
            </View>
            <View style={[s.podiumBar, { height: 70, backgroundColor: '#FFD700' }]}>
              <Text style={[s.podiumPos, { color: '#000' }]}>1</Text>
            </View>
            <Text style={[s.podiumName, { color: '#FFD700' }]} numberOfLines={1}>{data.rankings[0].name}</Text>
            <Text style={[s.podiumVal, { color: '#FFD700' }]}>{formatMoney(data.rankings[0].total_net_worth)}</Text>
          </View>
          {/* 3rd place */}
          <View style={s.podiumItem}>
            <View style={[s.podiumAvatar, { backgroundColor: AVATAR_COLORS[data.rankings[2].avatar_color] || '#FF9800', borderColor: '#CD7F32' }]}>
              <Ionicons name={(data.rankings[2].avatar_icon || 'person') as any} size={20} color="#fff" />
            </View>
            <View style={[s.podiumBar, { height: 35, backgroundColor: '#CD7F32' }]}>
              <Text style={s.podiumPos}>3</Text>
            </View>
            <Text style={s.podiumName} numberOfLines={1}>{data.rankings[2].name}</Text>
            <Text style={s.podiumVal}>{formatMoney(data.rankings[2].total_net_worth)}</Text>
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
            <View key={r.user_id} style={[s.rankRow, isMe && s.rankRowMe]}>
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
            </View>
          );
        })}

        {(!data?.rankings || data.rankings.length === 0) && (
          <View style={s.empty}>
            <Ionicons name="trophy-outline" size={48} color="#555" />
            <Text style={s.emptyText}>Nenhum ranking disponível</Text>
          </View>
        )}
      </ScrollView>
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
  // My Rank
  myRankCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginHorizontal: 16, backgroundColor: '#2a2a2a', borderRadius: 14, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: '#FFD700' },
  myRankLeft: { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 },
  myRankPos: { color: '#FFD700', fontSize: 18, fontWeight: 'bold', width: 40 },
  myRankName: { color: '#FFD700', fontSize: 15, fontWeight: 'bold' },
  myRankLevel: { color: '#888', fontSize: 12 },
  myRankRight: { alignItems: 'flex-end' },
  myRankValue: { color: '#FFD700', fontSize: 16, fontWeight: 'bold' },
  // Avatar
  avatar: { width: 34, height: 34, borderRadius: 17, justifyContent: 'center', alignItems: 'center' },
  // Podium
  podium: { flexDirection: 'row', justifyContent: 'center', alignItems: 'flex-end', paddingHorizontal: 16, paddingBottom: 12, gap: 8 },
  podiumItem: { alignItems: 'center', flex: 1 },
  podiumAvatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center', borderWidth: 2, marginBottom: 4 },
  podiumAvatarFirst: { width: 48, height: 48, borderRadius: 24, borderWidth: 3 },
  podiumBar: { width: '80%', borderTopLeftRadius: 8, borderTopRightRadius: 8, justifyContent: 'center', alignItems: 'center' },
  podiumPos: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  podiumName: { color: '#ccc', fontSize: 11, fontWeight: 'bold', marginTop: 4, textAlign: 'center' },
  podiumVal: { color: '#888', fontSize: 10, marginTop: 2 },
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
});
