import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { SkeletonList } from '../components/SkeletonLoader';
import { useHaptics } from '../hooks/useHaptics';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const ACH_NAMES: Record<string, Record<string, string>> = {
  first_job: { pt: 'Primeiro Emprego', en: 'First Job' },
  first_company: { pt: 'Primeira Empresa', en: 'First Company' },
  first_investment: { pt: 'Primeiro Investimento', en: 'First Investment' },
  millionaire: { pt: 'Milionário', en: 'Millionaire' },
  level_5: { pt: 'Nível 5', en: 'Level 5' },
  level_10: { pt: 'Nível 10', en: 'Level 10' },
  five_companies: { pt: '5 Empresas', en: '5 Companies' },
  ten_investments: { pt: '10 Investimentos', en: '10 Investments' },
  first_loan: { pt: 'Primeiro Empréstimo', en: 'First Loan' },
  collector: { pt: 'Colecionador', en: 'Collector' },
};

const ACH_DESC: Record<string, Record<string, string>> = {
  first_job: { pt: 'Conseguiu seu primeiro emprego', en: 'Got your first job' },
  first_company: { pt: 'Comprou sua primeira empresa', en: 'Bought your first company' },
  first_investment: { pt: 'Fez seu primeiro investimento', en: 'Made your first investment' },
  millionaire: { pt: 'Alcançou R$ 1.000.000', en: 'Reached $1,000,000' },
  level_5: { pt: 'Chegou ao nível 5', en: 'Reached level 5' },
  level_10: { pt: 'Chegou ao nível 10', en: 'Reached level 10' },
  five_companies: { pt: 'Possui 5 empresas', en: 'Own 5 companies' },
  ten_investments: { pt: '10 ativos no portfólio', en: '10 assets in portfolio' },
  first_loan: { pt: 'Pegou seu primeiro empréstimo', en: 'Took your first loan' },
  collector: { pt: 'Acumulou R$ 100.000', en: 'Accumulated $100,000' },
};

export default function Achievements() {
  const router = useRouter();
  const { token } = useAuth();
  const { t, locale } = useLanguage();
  const { trigger: haptic } = useHaptics();
  const [achievements, setAchievements] = useState<any[]>([]);
  const [stats, setStats] = useState({ total: 0, unlocked: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const lang = locale?.startsWith('pt') ? 'pt' : 'en';

  const loadData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      // Check for new achievements first
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/achievements/check`, {}, { headers });
      const res = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/achievements`, { headers });
      setAchievements(res.data.achievements);
      setStats({ total: res.data.total, unlocked: res.data.unlocked });
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  }, [token]);

  useEffect(() => { loadData(); }, []);

  if (loading) return <SafeAreaView style={s.container}><SkeletonList count={5} style={{ padding: 16, paddingTop: 60 }} /></SafeAreaView>;

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>{t('achievements.title')}</Text>
        <Text style={s.counter}>{stats.unlocked}/{stats.total}</Text>
      </View>

      {/* Progress Bar */}
      <View style={s.progressWrap}>
        <View style={[s.progressBar, { width: `${(stats.unlocked / stats.total) * 100}%` }]} />
      </View>

      <ScrollView
        style={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor="#4CAF50" />}
      >
        {achievements.map((ach) => (
          <View key={ach.id} style={[s.card, !ach.unlocked && s.cardLocked]}>
            <View style={[s.iconCircle, { backgroundColor: ach.unlocked ? ach.color + '22' : '#333' }]}>
              <Ionicons name={ach.icon} size={28} color={ach.unlocked ? ach.color : '#555'} />
            </View>
            <View style={s.info}>
              <Text style={[s.name, !ach.unlocked && s.textLocked]}>
                {ACH_NAMES[ach.id]?.[lang] || ach.id}
              </Text>
              <Text style={s.desc}>{ACH_DESC[ach.id]?.[lang] || ''}</Text>
              {ach.unlocked && (
                <Text style={s.reward}>+{ach.xp} XP  •  +${ach.money}</Text>
              )}
            </View>
            {ach.unlocked ? (
              <Ionicons name="checkmark-circle" size={28} color={ach.color} />
            ) : (
              <Ionicons name="lock-closed" size={24} color="#555" />
            )}
          </View>
        ))}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  back: { padding: 4 },
  title: { flex: 1, fontSize: 22, fontWeight: 'bold', color: '#fff' },
  counter: { fontSize: 18, fontWeight: 'bold', color: '#4CAF50' },
  progressWrap: { height: 4, backgroundColor: '#333', marginHorizontal: 16, borderRadius: 2 },
  progressBar: { height: 4, backgroundColor: '#4CAF50', borderRadius: 2 },
  list: { flex: 1, padding: 16 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1a1a2e', borderRadius: 14, padding: 16, marginBottom: 10, gap: 14 },
  cardLocked: { opacity: 0.5 },
  iconCircle: { width: 52, height: 52, borderRadius: 26, justifyContent: 'center', alignItems: 'center' },
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  textLocked: { color: '#888' },
  desc: { fontSize: 13, color: '#aaa', marginTop: 2 },
  reward: { fontSize: 12, color: '#4CAF50', marginTop: 4, fontWeight: '600' },
});
