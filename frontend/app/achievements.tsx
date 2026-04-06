import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Platform, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { useSound } from '../context/SoundContext';
import { SkeletonList } from '../components/SkeletonLoader';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const GROUP_NAMES: Record<string, Record<string, string>> = {
  jobs: { pt: 'Empregos', en: 'Jobs', es: 'Empleos', zh: '工作', de: 'Jobs', fr: 'Emplois', it: 'Lavori' },
  companies: { pt: 'Empresas', en: 'Companies', es: 'Empresas', zh: '企业', de: 'Firmen', fr: 'Entreprises', it: 'Aziende' },
  investments: { pt: 'Investimentos', en: 'Investments', es: 'Inversiones', zh: '投资', de: 'Investitionen', fr: 'Investissements', it: 'Investimenti' },
  money: { pt: 'Dinheiro', en: 'Money', es: 'Dinero', zh: '资金', de: 'Geld', fr: 'Argent', it: 'Denaro' },
  level: { pt: 'Nível', en: 'Level', es: 'Nivel', zh: '等级', de: 'Level', fr: 'Niveau', it: 'Livello' },
  education: { pt: 'Educação', en: 'Education', es: 'Educación', zh: '教育', de: 'Bildung', fr: 'Éducation', it: 'Istruzione' },
  certifications: { pt: 'Certificações', en: 'Certifications', es: 'Certificaciones', zh: '证书', de: 'Zertifikate', fr: 'Certifications', it: 'Certificazioni' },
  courses: { pt: 'Cursos', en: 'Courses', es: 'Cursos', zh: '课程', de: 'Kurse', fr: 'Cours', it: 'Corsi' },
  assets: { pt: 'Patrimônio', en: 'Assets', es: 'Activos', zh: '资产', de: 'Vermögen', fr: 'Actifs', it: 'Patrimonio' },
  loans: { pt: 'Empréstimos', en: 'Loans', es: 'Préstamos', zh: '贷款', de: 'Kredite', fr: 'Prêts', it: 'Prestiti' },
  franchises: { pt: 'Franquias', en: 'Franchises', es: 'Franquicias', zh: '加盟店', de: 'Franchises', fr: 'Franchises', it: 'Franchising' },
  net_worth: { pt: 'Patrimônio Líquido', en: 'Net Worth', es: 'Patrimonio Neto', zh: '净资产', de: 'Nettowert', fr: 'Valeur Nette', it: 'Patrimonio Netto' },
};

const GROUP_DESC: Record<string, Record<string, string>> = {
  jobs: { pt: 'Trabalhe em diferentes empregos', en: 'Work at different jobs' },
  companies: { pt: 'Compre e crie empresas', en: 'Buy and create companies' },
  investments: { pt: 'Invista no mercado financeiro', en: 'Invest in the market' },
  money: { pt: 'Acumule dinheiro em caixa', en: 'Accumulate cash money' },
  level: { pt: 'Suba de nível no jogo', en: 'Level up in the game' },
  education: { pt: 'Complete formações acadêmicas', en: 'Complete education degrees' },
  certifications: { pt: 'Obtenha certificações profissionais', en: 'Get professional certifications' },
  courses: { pt: 'Complete cursos de universidades', en: 'Complete university courses' },
  assets: { pt: 'Compre imóveis e veículos', en: 'Buy real estate and vehicles' },
  loans: { pt: 'Utilize o sistema bancário', en: 'Use the banking system' },
  franchises: { pt: 'Crie franquias de suas empresas', en: 'Create company franchises' },
  net_worth: { pt: 'Aumente seu patrimônio total', en: 'Increase your total net worth' },
};

function formatTarget(group: string, target: number): string {
  if (group === 'money' || group === 'net_worth') {
    if (target >= 1_000_000_000) return `${(target / 1_000_000_000).toFixed(0)}B`;
    if (target >= 1_000_000) return `${(target / 1_000_000).toFixed(0)}M`;
    if (target >= 1_000) return `${(target / 1_000).toFixed(0)}K`;
    return `${target}`;
  }
  return `${target}`;
}

function formatReward(money: number): string {
  if (money >= 1_000_000) return `${(money / 1_000_000).toFixed(0)}M`;
  if (money >= 1_000) return `${(money / 1_000).toFixed(0)}K`;
  return `${money}`;
}

export default function Achievements() {
  const router = useRouter();
  const { token } = useAuth();
  const { t, locale, formatMoney: fm } = useLanguage();
  const { colors, isDark } = useTheme();
  const { playSuccess } = useSound();
  const [groups, setGroups] = useState<any[]>([]);
  const [stats, setStats] = useState({ total: 0, unlocked: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

  const lang = locale?.startsWith('pt') ? 'pt' : locale?.startsWith('es') ? 'es' : locale?.startsWith('zh') ? 'zh' : locale?.startsWith('de') ? 'de' : locale?.startsWith('fr') ? 'fr' : locale?.startsWith('it') ? 'it' : 'en';

  const loadData = useCallback(async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const checkRes = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/achievements/check`, {}, { headers });
      if (checkRes.data.count > 0) {
        playSuccess();
        const msg = `+${checkRes.data.xp_earned} XP  •  +$${checkRes.data.money_earned.toLocaleString()}`;
        if (Platform.OS === 'web') {
          window.alert?.(`Conquista Desbloqueada!\n${msg}`);
        } else {
          Alert.alert('Conquista Desbloqueada!', msg);
        }
      }
      const res = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/achievements`, { headers });
      setGroups(res.data.achievements);
      setStats({ total: res.data.total, unlocked: res.data.unlocked });
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  }, [token]);

  useEffect(() => { if (token) loadData(); }, [token]);

  if (loading) return <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}><SkeletonList count={6} style={{ padding: 16, paddingTop: 60 }} /></SafeAreaView>;

  const progressPct = stats.total > 0 ? (stats.unlocked / stats.total * 100) : 0;

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={[s.header, { borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={[s.title, { color: colors.text }]}>{t('achievements.title') || 'Conquistas'}</Text>
          <Text style={{ color: colors.textSecondary, fontSize: 12 }}>{stats.unlocked}/{stats.total} {t('achievements.unlocked') || 'desbloqueadas'}</Text>
        </View>
        <View style={s.counterBadge}>
          <Text style={s.counterText}>{Math.round(progressPct)}%</Text>
        </View>
      </View>

      {/* Global Progress */}
      <View style={{ paddingHorizontal: 16, paddingVertical: 8 }}>
        <View style={{ height: 6, backgroundColor: isDark ? '#333' : '#ddd', borderRadius: 3 }}>
          <View style={{ height: 6, backgroundColor: '#4CAF50', borderRadius: 3, width: `${progressPct}%` }} />
        </View>
      </View>

      <ScrollView
        style={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} tintColor="#4CAF50" />}
      >
        {groups.map((group) => {
          const isExpanded = expandedGroup === group.group;
          const nextTier = group.next_tier;
          const groupName = GROUP_NAMES[group.group]?.[lang] || GROUP_NAMES[group.group]?.['en'] || group.group;
          const groupDesc = GROUP_DESC[group.group]?.[lang] || GROUP_DESC[group.group]?.['en'] || '';

          return (
            <View key={group.group} style={[s.groupCard, { backgroundColor: isDark ? '#1a1a2e' : '#fff', borderColor: isDark ? '#2a2a3e' : '#e0e0e0' }]}>
              {/* Group Header */}
              <TouchableOpacity
                style={s.groupHeader}
                onPress={() => setExpandedGroup(isExpanded ? null : group.group)}
                activeOpacity={0.7}
              >
                <View style={[s.groupIcon, { backgroundColor: group.color + '22' }]}>
                  <Ionicons name={group.icon as any} size={24} color={group.color} />
                </View>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <Text style={[s.groupName, { color: colors.text }]}>{groupName}</Text>
                    <View style={[s.tierBadge, { backgroundColor: group.color + '22' }]}>
                      <Text style={[s.tierBadgeText, { color: group.color }]}>
                        {group.completed_tiers}/{group.total_tiers}
                      </Text>
                    </View>
                    {group.all_done && <Text style={{ fontSize: 14 }}>⭐</Text>}
                  </View>
                  {!group.all_done && nextTier ? (
                    <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 2 }}>
                      {t('achievements.nextGoal') || 'Próximo'}: {formatTarget(group.group, nextTier.target)} • 💰 {fm(nextTier.money)}
                    </Text>
                  ) : (
                    <Text style={{ color: '#4CAF50', fontSize: 12, marginTop: 2, fontWeight: '600' }}>
                      {t('achievements.allComplete') || 'Todas concluídas!'} ✅
                    </Text>
                  )}
                </View>

                {/* Mini progress */}
                <View style={{ alignItems: 'flex-end', gap: 4 }}>
                  {!group.all_done && nextTier && (
                    <Text style={{ color: group.color, fontSize: 13, fontWeight: 'bold' }}>
                      💰 {fm(nextTier.money)}
                    </Text>
                  )}
                  <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={18} color={colors.textSecondary} />
                </View>
              </TouchableOpacity>

              {/* Progress bar */}
              <View style={{ paddingHorizontal: 16, paddingBottom: isExpanded ? 4 : 12 }}>
                <View style={{ height: 4, backgroundColor: isDark ? '#333' : '#e0e0e0', borderRadius: 2 }}>
                  <View style={{ height: 4, backgroundColor: group.color, borderRadius: 2, width: `${group.progress_pct}%` }} />
                </View>
              </View>

              {/* Expanded Tiers */}
              {isExpanded && (
                <View style={[s.tiersContainer, { borderTopColor: isDark ? '#2a2a3e' : '#e0e0e0' }]}>
                  <Text style={{ color: colors.textSecondary, fontSize: 11, paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 }}>{groupDesc}</Text>
                  {group.tiers.map((tier: any, idx: number) => {
                    const isNext = !tier.unlocked && (!group.tiers[idx - 1] || group.tiers[idx - 1].unlocked);
                    return (
                      <View key={tier.id} style={[s.tierRow, isNext && { backgroundColor: group.color + '08' }]}>
                        <View style={[s.tierDot, { backgroundColor: tier.unlocked ? group.color : (isNext ? group.color + '55' : '#444') }]}>
                          {tier.unlocked ? (
                            <Ionicons name="checkmark" size={12} color="#fff" />
                          ) : (
                            <Text style={{ color: '#888', fontSize: 10, fontWeight: 'bold' }}>{idx + 1}</Text>
                          )}
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={{ color: tier.unlocked ? colors.text : colors.textSecondary, fontSize: 14, fontWeight: tier.unlocked || isNext ? '600' : '400' }}>
                            {formatTarget(group.group, tier.target)} {group.group === 'money' || group.group === 'net_worth' ? '' : groupName.toLowerCase()}
                          </Text>
                        </View>
                        <View style={{ alignItems: 'flex-end' }}>
                          <Text style={{ color: tier.unlocked ? '#4CAF50' : (isNext ? group.color : '#666'), fontSize: 13, fontWeight: 'bold' }}>
                            💰 {fm(tier.money)}
                          </Text>
                          <Text style={{ color: tier.unlocked ? '#4CAF50' : '#888', fontSize: 10 }}>
                            +{tier.xp} XP
                          </Text>
                        </View>
                        {tier.unlocked && <Ionicons name="checkmark-circle" size={18} color="#4CAF50" style={{ marginLeft: 6 }} />}
                      </View>
                    );
                  })}
                </View>
              )}
            </View>
          );
        })}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12, borderBottomWidth: 1 },
  back: { padding: 4 },
  title: { fontSize: 22, fontWeight: 'bold' },
  counterBadge: { backgroundColor: '#4CAF50', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6 },
  counterText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  list: { flex: 1, padding: 12 },
  groupCard: { borderRadius: 14, marginBottom: 10, borderWidth: 1, overflow: 'hidden' },
  groupHeader: { flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
  groupIcon: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
  groupName: { fontSize: 16, fontWeight: 'bold' },
  tierBadge: { borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  tierBadgeText: { fontSize: 11, fontWeight: 'bold' },
  tiersContainer: { borderTopWidth: 1, paddingBottom: 8 },
  tierRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 10, gap: 10 },
  tierDot: { width: 24, height: 24, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
});
