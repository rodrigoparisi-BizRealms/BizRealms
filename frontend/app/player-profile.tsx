import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function PlayerProfile() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { token } = useAuth();
  const { t, formatMoney } = useLanguage();
  const { colors } = useTheme();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id || !token) return;
    axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/user/profile/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => setProfile(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id, token]);

  const getAvatarColor = (color: string) => color || '#4CAF50';

  const ComparisonBadge = ({ myVal, theirVal, label, isMoney = false }: any) => {
    const diff = myVal - theirVal;
    const better = diff > 0;
    const equal = diff === 0;
    return (
      <View style={s.compRow}>
        <Text style={[s.compLabel, { color: colors.textSecondary }]}>{label}</Text>
        <View style={s.compValues}>
          <View style={[s.compCol, { backgroundColor: colors.card }]}>
            <Text style={[s.compColLabel, { color: colors.textSecondary }]}>{t('profile.you')}</Text>
            <Text style={[s.compVal, { color: colors.text }, better && { color: '#4CAF50' }]}>{isMoney ? formatMoney(myVal) : myVal}</Text>
          </View>
          <View style={s.compVs}>
            <Ionicons name={equal ? 'swap-horizontal' : better ? 'chevron-up' : 'chevron-down'} size={16} color={equal ? '#888' : better ? '#4CAF50' : '#F44336'} />
          </View>
          <View style={[s.compCol, { backgroundColor: colors.card }]}>
            <Text style={[s.compColLabel, { color: colors.textSecondary }]}>{profile?.name?.split(' ')[0] || t('profile.player')}</Text>
            <Text style={[s.compVal, { color: colors.text }, !better && !equal && { color: '#4CAF50' }]}>{isMoney ? formatMoney(theirVal) : theirVal}</Text>
          </View>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
        <View style={[s.header, { borderBottomColor: colors.border }]}>
          <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={[s.headerTitle, { color: colors.text }]}>{t('profile.publicProfile')}</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={s.center}><ActivityIndicator size="large" color="#4CAF50" /></View>
      </SafeAreaView>
    );
  }

  if (!profile) {
    return (
      <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
        <View style={[s.header, { borderBottomColor: colors.border }]}>
          <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={[s.headerTitle, { color: colors.text }]}>{t('profile.publicProfile')}</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={s.center}><Text style={[s.errorText, { color: colors.textSecondary }]}>{t('profile.playerNotFound')}</Text></View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={[s.header, { borderBottomColor: colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[s.headerTitle, { color: colors.text }]}>{t('profile.publicProfile')}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={s.content}>
        {/* Player Card */}
        <View style={[s.playerCard, { backgroundColor: colors.card }]}>
          <View style={[s.avatar, { backgroundColor: getAvatarColor(profile.avatar_color) }]}>
            <Text style={s.avatarText}>{(profile.name || 'J')[0].toUpperCase()}</Text>
          </View>
          <Text style={[s.playerName, { color: colors.text }]}>{profile.name}</Text>
          <View style={[s.levelBadge, { backgroundColor: colors.background }]}>
            <Ionicons name="star" size={14} color="#FFD700" />
            <Text style={s.levelText}>{t('profile.levelLabel')} {profile.level}</Text>
          </View>
          <Text style={s.moneyText}>{formatMoney(profile.money)}</Text>
          {profile.background ? <Text style={[s.bgText, { color: colors.textSecondary }]}>{profile.background}</Text> : null}
        </View>

        {/* Stats Grid */}
        <View style={s.statsGrid}>
          <View style={[s.statItem, { backgroundColor: colors.card }]}>
            <Ionicons name="business" size={20} color="#4CAF50" />
            <Text style={[s.statNum, { color: colors.text }]}>{profile.companies_count}</Text>
            <Text style={[s.statLabel, { color: colors.textSecondary }]}>{t('general.companies') || t('home.companies')}</Text>
          </View>
          <View style={[s.statItem, { backgroundColor: colors.card }]}>
            <Ionicons name="trending-up" size={20} color="#2196F3" />
            <Text style={[s.statNum, { color: colors.text }]}>{profile.investments_count}</Text>
            <Text style={[s.statLabel, { color: colors.textSecondary }]}>{t('general.investments') || t('home.investments')}</Text>
          </View>
          <View style={[s.statItem, { backgroundColor: colors.card }]}>
            <Ionicons name="home" size={20} color="#FF9800" />
            <Text style={[s.statNum, { color: colors.text }]}>{profile.assets_count}</Text>
            <Text style={[s.statLabel, { color: colors.textSecondary }]}>{t('general.assets') || t('home.assets')}</Text>
          </View>
          <View style={[s.statItem, { backgroundColor: colors.card }]}>
            <Ionicons name="school" size={20} color="#9C27B0" />
            <Text style={[s.statNum, { color: colors.text }]}>{profile.education_count}</Text>
            <Text style={[s.statLabel, { color: colors.textSecondary }]}>{t('general.education') || t('home.education')}</Text>
          </View>
          <View style={[s.statItem, { backgroundColor: colors.card }]}>
            <Ionicons name="ribbon" size={20} color="#E91E63" />
            <Text style={[s.statNum, { color: colors.text }]}>{profile.certification_count}</Text>
            <Text style={[s.statLabel, { color: colors.textSecondary }]}>{t('general.certifications') || t('home.certifications')}</Text>
          </View>
          <View style={[s.statItem, { backgroundColor: colors.card }]}>
            <Ionicons name="briefcase" size={20} color="#607D8B" />
            <Text style={[s.statNum, { color: colors.text }]}>{profile.work_experience_count}</Text>
            <Text style={[s.statLabel, { color: colors.textSecondary }]}>{t('general.jobs') || t('home.jobsLabel')}</Text>
          </View>
        </View>

        {/* Comparison Section */}
        <View style={[s.compSection, { backgroundColor: colors.card }]}>
          <Text style={[s.compTitle, { color: colors.text }]}>{t('profile.comparison')}</Text>
          <ComparisonBadge myVal={profile.comparison.my_level} theirVal={profile.level} label={t('profile.levelLabel')} />
          <ComparisonBadge myVal={profile.comparison.my_money} theirVal={profile.money} label={t('general.money') || t('home.money')} isMoney />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1 },
  backBtn: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 18, fontWeight: 'bold' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  errorText: { fontSize: 16 },
  content: { padding: 16, gap: 16 },
  playerCard: { borderRadius: 16, padding: 24, alignItems: 'center', gap: 8 },
  avatar: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontSize: 32, fontWeight: 'bold' },
  playerName: { fontSize: 22, fontWeight: 'bold' },
  levelBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20 },
  levelText: { color: '#FFD700', fontSize: 14, fontWeight: '600' },
  moneyText: { color: '#4CAF50', fontSize: 18, fontWeight: 'bold' },
  bgText: { fontSize: 13 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  statItem: { width: '31%', borderRadius: 12, padding: 14, alignItems: 'center', gap: 4 },
  statNum: { fontSize: 20, fontWeight: 'bold' },
  statLabel: { fontSize: 11, textAlign: 'center' },
  compSection: { borderRadius: 16, padding: 16, gap: 12 },
  compTitle: { fontSize: 16, fontWeight: 'bold', textAlign: 'center', marginBottom: 4 },
  compRow: { gap: 6 },
  compLabel: { fontSize: 12, textAlign: 'center' },
  compValues: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  compCol: { flex: 1, alignItems: 'center', borderRadius: 10, paddingVertical: 10 },
  compColLabel: { fontSize: 11 },
  compVal: { fontSize: 16, fontWeight: 'bold' },
  compVs: { width: 30, alignItems: 'center' },
});
