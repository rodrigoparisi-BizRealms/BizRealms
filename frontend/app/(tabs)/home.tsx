import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Image,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { useSounds } from '../../hooks/useSounds';
import { useLanguage } from '../../context/LanguageContext';
import TutorialOverlay from '../../components/TutorialOverlay';
import { SkeletonStats, SkeletonList } from '../../components/SkeletonLoader';
import { useHaptics } from '../../hooks/useHaptics';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const getAvatarColor = (color: string) => {
  const colors: Record<string, string> = {
    green: '#4CAF50',
    blue: '#2196F3',
    purple: '#9C27B0',
    orange: '#FF9800',
    red: '#F44336',
    yellow: '#FFC107',
  };
  return colors[color] || '#4CAF50';
};

export default function Home() {
  const { user, token, refreshUser } = useAuth();
  const router = useRouter();
  const { play } = useSounds();
  const { trigger: haptic } = useHaptics();
  const { t, formatMoney } = useLanguage();
  const fm = (v: number) => formatMoney(v, true);
  const [stats, setStats] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [companies, setCompanies] = useState<any>(null);
  const [assets, setAssets] = useState<any>(null);
  const [rankings, setRankings] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadAllData = useCallback(async () => {
    if (!token) return;
    const h = { Authorization: `Bearer ${token}` };
    try {
      const [statsRes, portfolioRes, companiesRes, assetsRes, rankingsRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/user/stats`, { headers: h }).catch(() => null),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/investments/portfolio`, { headers: h }).catch(() => null),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/owned`, { headers: h }).catch(() => null),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/owned`, { headers: h }).catch(() => null),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/rankings?period=weekly`, { headers: h }).catch(() => null),
      ]);
      if (statsRes) setStats(statsRes.data);
      if (portfolioRes) setPortfolio(portfolioRes.data);
      if (companiesRes) setCompanies(companiesRes.data);
      if (assetsRes) setAssets(assetsRes.data);
      if (rankingsRes) setRankings(rankingsRes.data);
    } catch (e) {
      console.error('Error loading dashboard:', e);
    }
  }, [token]);

  useEffect(() => { loadAllData(); }, [loadAllData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshUser();
    await loadAllData();
    setRefreshing(false);
  };

  if (!user || !stats) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={{ flex: 1, padding: 16, paddingTop: 40 }}>
          <SkeletonStats />
          <SkeletonList count={4} style={{ marginTop: 24 }} />
        </View>
      </SafeAreaView>
    );
  }

  const levelProgress = (stats.experience_points % 1000) / 10;

  // Calculate total net worth
  const cashMoney = user.money || 0;
  const investmentValue = portfolio?.summary?.total_current_value || 0;
  const companiesRevenue = companies?.total_monthly_revenue || 0;
  const assetsValue = assets?.summary?.total_value || 0;
  const totalNetWorth = cashMoney + investmentValue + assetsValue;

  const investmentProfit = portfolio?.summary?.total_profit || 0;
  const investmentProfitPct = portfolio?.summary?.total_profit_pct || 0;
  const numPositions = portfolio?.summary?.num_positions || 0;

  const numCompanies = companies?.count || 0;
  const numAssets = assets?.summary?.count || 0;
  const assetsProfit = assets?.summary?.total_profit || 0;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            {(user as any).avatar_photo ? (
              <Image
                source={{ uri: (user as any).avatar_photo }}
                style={styles.avatarImage}
              />
            ) : (
              <View
                style={[
                  styles.avatar,
                  { backgroundColor: getAvatarColor(user.avatar_color || 'green') },
                ]}
              >
                <Ionicons
                  name={(user.avatar_icon || 'person') as any}
                  size={32}
                  color="#fff"
                />
              </View>
            )}
            <View style={{ flexShrink: 1 }}>
              <Text style={styles.greeting} numberOfLines={1}>{t('home.greeting')}, {user.name}!</Text>
              <Text style={styles.location}>
                <Ionicons name="location" size={14} color="#888" /> {user.location}
              </Text>
            </View>
          </View>
          <View style={styles.levelBadge}>
            <Text style={styles.levelText}>{t('home.lv')} {stats.level}</Text>
          </View>
        </View>

        {/* Net Worth Card */}
        <View style={styles.netWorthCard}>
          <View style={styles.netWorthHeader}>
            <Ionicons name="trophy" size={22} color="#FFD700" />
            <Text style={styles.netWorthLabel}>{t('home.netWorth')}</Text>
          </View>
          <Text style={styles.netWorthValue}>
            {formatMoney(totalNetWorth)}
          </Text>
          <View style={styles.netWorthBreakdown}>
            <View style={styles.breakdownItem}>
              <View style={[styles.breakdownDot, { backgroundColor: '#4CAF50' }]} />
              <Text style={styles.breakdownLabel}>{t('home.cash')}</Text>
              <Text style={styles.breakdownValue}>{fm(cashMoney)}</Text>
            </View>
            <View style={styles.breakdownItem}>
              <View style={[styles.breakdownDot, { backgroundColor: '#2196F3' }]} />
              <Text style={styles.breakdownLabel}>{t('home.investmentsLabel')}</Text>
              <Text style={styles.breakdownValue}>{fm(investmentValue)}</Text>
            </View>
            <View style={styles.breakdownItem}>
              <View style={[styles.breakdownDot, { backgroundColor: '#9C27B0' }]} />
              <Text style={styles.breakdownLabel}>{t('home.assetsLabel')}</Text>
              <Text style={styles.breakdownValue}>{fm(assetsValue)}</Text>
            </View>
          </View>
        </View>

        {/* Experience Progress */}
        <View style={styles.expCard}>
          <View style={styles.expHeader}>
            <Text style={styles.expLabel}>{t('home.experience')}</Text>
            <Text style={styles.expValue}>
              {stats.experience_points} / {stats.next_level_exp} XP
            </Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${levelProgress}%` }]} />
          </View>
        </View>

        {/* Rankings Panel */}
        <TouchableOpacity
          style={[styles.panelCard, { borderWidth: 1, borderColor: '#FFD70030' }]}
          onPress={() => { play('click'); router.push('/rankings'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(255,215,0,0.15)' }]}>
                <Ionicons name="trophy" size={20} color="#FFD700" />
              </View>
              <Text style={styles.panelTitle}>{t('home.weeklyRanking')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          {rankings?.current_user ? (
            <View style={{ gap: 8 }}>
              <View style={styles.panelMainRow}>
                <View>
                  <Text style={[styles.panelBigValue, { color: '#FFD700' }]}>
                    #{rankings.current_user.position}
                  </Text>
                  <Text style={styles.panelSubLabel}>
                    {t('home.ofPlayers')} {rankings.total_players} {t('home.players')}
                  </Text>
                </View>
                <View style={[styles.profitBadge, { backgroundColor: 'rgba(255,215,0,0.15)' }]}>
                  <Ionicons name="trophy" size={14} color="#FFD700" />
                  <Text style={[styles.profitText, { color: '#FFD700' }]}>
                    {fm(rankings.current_user.total_net_worth)}
                  </Text>
                </View>
              </View>
              {/* Mini Top 3 */}
              {rankings.rankings?.slice(0, 3).map((r: any, i: number) => (
                <View key={r.user_id} style={styles.miniHolding}>
                  <Text style={{
                    color: i === 0 ? '#FFD700' : i === 1 ? '#C0C0C0' : '#CD7F32',
                    fontSize: 14, fontWeight: 'bold', width: 24
                  }}>
                    {i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉'}
                  </Text>
                  <Text style={styles.miniTicker} numberOfLines={1}>
                    {r.user_id === user?.id ? t('home.you') : r.name}
                  </Text>
                  <Text style={[styles.miniProfit, { color: '#FFD700' }]}>
                    {fm(r.total_net_worth)}
                  </Text>
                </View>
              ))}
            </View>
          ) : (
            <View style={styles.panelEmpty}>
              <Text style={styles.panelEmptyText}>{t('home.rankAvailable')}</Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Bank Panel */}
        <TouchableOpacity
          style={[styles.panelCard, { borderWidth: 1, borderColor: '#1E88E530' }]}
          onPress={() => { play('click'); router.push('/(tabs)/bank'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(30,136,229,0.15)' }]}>
                <Ionicons name="card" size={20} color="#1E88E5" />
              </View>
              <Text style={styles.panelTitle}>{t('home.bank')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          <View style={styles.panelEmpty}>
            <Text style={[styles.panelEmptyText, { color: '#1E88E5' }]}>{t('home.bankDesc')}</Text>
            <Text style={styles.panelEmptyHint}>{t('home.bankHint')}</Text>
          </View>
        </TouchableOpacity>

        {/* Courses Panel */}
        <TouchableOpacity
          style={[styles.panelCard, { borderWidth: 1, borderColor: '#4CAF5030' }]}
          onPress={() => { play('click'); router.push('/(tabs)/courses'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(76,175,80,0.15)' }]}>
                <Ionicons name="school" size={20} color="#4CAF50" />
              </View>
              <Text style={styles.panelTitle}>{t('home.courses')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          <View style={styles.panelEmpty}>
            <Text style={[styles.panelEmptyText, { color: '#4CAF50' }]}>{t('home.coursesDesc')}</Text>
            <Text style={styles.panelEmptyHint}>{t('home.coursesHint')}</Text>
          </View>
        </TouchableOpacity>

        {/* Music Panel */}
        <TouchableOpacity
          style={[styles.panelCard, { borderWidth: 1, borderColor: '#9C27B030' }]}
          onPress={() => { play('click'); router.push('/(tabs)/music'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(156,39,176,0.15)' }]}>
                <Ionicons name="musical-notes" size={20} color="#9C27B0" />
              </View>
              <Text style={styles.panelTitle}>{t('home.music')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          <View style={styles.panelEmpty}>
            <Text style={[styles.panelEmptyText, { color: '#9C27B0' }]}>{t('home.musicDesc')}</Text>
            <Text style={styles.panelEmptyHint}>{t('home.musicHint')}</Text>
          </View>
        </TouchableOpacity>

        {/* AI Coach Panel */}
        <TouchableOpacity
          style={[styles.panelCard, { borderWidth: 1, borderColor: '#FFD70030' }]}
          onPress={() => { play('click'); router.push('/(tabs)/coaching'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(255,215,0,0.15)' }]}>
                <Ionicons name="sparkles" size={20} color="#FFD700" />
              </View>
              <Text style={styles.panelTitle}>{t('home.coach')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          <View style={styles.panelEmpty}>
            <Text style={[styles.panelEmptyText, { color: '#FFD700' }]}>{t('home.coachDesc')}</Text>
            <Text style={styles.panelEmptyHint}>{t('home.coachHint')}</Text>
          </View>
        </TouchableOpacity>

        {/* Investment Portfolio Panel */}
        <TouchableOpacity
          style={styles.panelCard}
          onPress={() => { play('click'); router.push('/(tabs)/investments'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(33,150,243,0.15)' }]}>
                <Ionicons name="trending-up" size={20} color="#2196F3" />
              </View>
              <Text style={styles.panelTitle}>{t('home.investments')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          {numPositions > 0 ? (
            <>
              <View style={styles.panelMainRow}>
                <View>
                  <Text style={styles.panelBigValue}>{formatMoney(investmentValue)}</Text>
                  <Text style={styles.panelSubLabel}>Valor atual</Text>
                </View>
                <View style={[
                  styles.profitBadge,
                  { backgroundColor: investmentProfit >= 0 ? 'rgba(76,175,80,0.15)' : 'rgba(244,67,54,0.15)' }
                ]}>
                  <Ionicons
                    name={investmentProfit >= 0 ? 'arrow-up' : 'arrow-down'}
                    size={14}
                    color={investmentProfit >= 0 ? '#4CAF50' : '#F44336'}
                  />
                  <Text style={[
                    styles.profitText,
                    { color: investmentProfit >= 0 ? '#4CAF50' : '#F44336' }
                  ]}>
                    {investmentProfit >= 0 ? '+' : ''}{investmentProfitPct.toFixed(1)}%
                  </Text>
                </View>
              </View>
              <View style={styles.panelDetailRow}>
                <View style={styles.panelDetail}>
                  <Text style={styles.detailLabel}>Posições</Text>
                  <Text style={styles.detailValue}>{numPositions}</Text>
                </View>
                <View style={styles.panelDetail}>
                  <Text style={styles.detailLabel}>Investido</Text>
                  <Text style={styles.detailValue}>{formatMoney(portfolio?.summary?.total_invested || 0)}</Text>
                </View>
                <View style={styles.panelDetail}>
                  <Text style={styles.detailLabel}>Lucro/Prej.</Text>
                  <Text style={[styles.detailValue, { color: investmentProfit >= 0 ? '#4CAF50' : '#F44336' }]}>
                    {investmentProfit >= 0 ? '+' : ''}{formatMoney(Math.abs(investmentProfit))}
                  </Text>
                </View>
              </View>
              {/* Mini Holdings List */}
              {portfolio?.holdings?.slice(0, 3).map((h: any) => (
                <View key={h.asset_id} style={styles.miniHolding}>
                  <Text style={styles.miniTicker}>{h.ticker || h.asset_name}</Text>
                  <Text style={styles.miniQty}>{h.quantity?.toFixed(h.quantity < 1 ? 4 : 2)}</Text>
                  <Text style={[
                    styles.miniProfit,
                    { color: (h.profit || 0) >= 0 ? '#4CAF50' : '#F44336' }
                  ]}>
                    {(h.profit_pct || 0) >= 0 ? '+' : ''}{(h.profit_pct || 0).toFixed(1)}%
                  </Text>
                </View>
              ))}
              {(portfolio?.holdings?.length || 0) > 3 && (
                <Text style={styles.seeMore}>+{portfolio.holdings.length - 3} mais...</Text>
              )}
            </>
          ) : (
            <View style={styles.panelEmpty}>
              <Text style={styles.panelEmptyText}>Nenhum investimento ainda</Text>
              <Text style={styles.panelEmptyHint}>Comece investindo em ações, cripto e mais</Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Companies Panel */}
        <TouchableOpacity
          style={styles.panelCard}
          onPress={() => { play('click'); router.push('/(tabs)/companies'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(76,175,80,0.15)' }]}>
                <Ionicons name="business" size={20} color="#4CAF50" />
              </View>
              <Text style={styles.panelTitle}>Empresas</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          {numCompanies > 0 ? (
            <>
              <View style={styles.panelMainRow}>
                <View>
                  <Text style={[styles.panelBigValue, { color: '#4CAF50' }]}>{formatMoney(companiesRevenue)}/mês</Text>
                  <Text style={styles.panelSubLabel}>Receita mensal</Text>
                </View>
                <View style={[styles.profitBadge, { backgroundColor: 'rgba(76,175,80,0.15)' }]}>
                  <Ionicons name="business" size={14} color="#4CAF50" />
                  <Text style={[styles.profitText, { color: '#4CAF50' }]}>{numCompanies} empresa{numCompanies > 1 ? 's' : ''}</Text>
                </View>
              </View>
              {/* Mini Companies List */}
              {companies?.companies?.slice(0, 3).map((c: any) => (
                <View key={c.id} style={styles.miniHolding}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, gap: 8 }}>
                    <View style={[styles.miniIcon, { backgroundColor: c.color || '#4CAF50' }]}>
                      <Ionicons name={(c.icon || 'business') as any} size={12} color="#fff" />
                    </View>
                    <Text style={styles.miniTicker} numberOfLines={1}>{c.name}</Text>
                  </View>
                  <Text style={[styles.miniProfit, { color: '#4CAF50' }]}>
                    R$ {(c.effective_revenue || c.monthly_revenue || 0).toLocaleString('pt-BR')}/mês
                  </Text>
                </View>
              ))}
            </>
          ) : (
            <View style={styles.panelEmpty}>
              <Text style={styles.panelEmptyText}>Nenhuma empresa</Text>
              <Text style={styles.panelEmptyHint}>Compre ou crie empresas para gerar renda passiva</Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Assets Panel */}
        <TouchableOpacity
          style={styles.panelCard}
          onPress={() => { play('click'); router.push('/(tabs)/patrimonio'); }}
          activeOpacity={0.7}
        >
          <View style={styles.panelHeader}>
            <View style={styles.panelTitleRow}>
              <View style={[styles.panelIconBg, { backgroundColor: 'rgba(156,39,176,0.15)' }]}>
                <Ionicons name="diamond" size={20} color="#9C27B0" />
              </View>
              <Text style={styles.panelTitle}>Bens e Imóveis</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#555" />
          </View>
          {numAssets > 0 ? (
            <>
              <View style={styles.panelMainRow}>
                <View>
                  <Text style={[styles.panelBigValue, { color: '#9C27B0' }]}>{formatMoney(assetsValue)}</Text>
                  <Text style={styles.panelSubLabel}>Valor total</Text>
                </View>
                <View style={[
                  styles.profitBadge,
                  { backgroundColor: assetsProfit >= 0 ? 'rgba(76,175,80,0.15)' : 'rgba(244,67,54,0.15)' }
                ]}>
                  <Ionicons
                    name={assetsProfit >= 0 ? 'arrow-up' : 'arrow-down'}
                    size={14}
                    color={assetsProfit >= 0 ? '#4CAF50' : '#F44336'}
                  />
                  <Text style={[
                    styles.profitText,
                    { color: assetsProfit >= 0 ? '#4CAF50' : '#F44336' }
                  ]}>
                    {assetsProfit >= 0 ? '+' : ''}{formatMoney(Math.abs(assetsProfit))}
                  </Text>
                </View>
              </View>
              <View style={styles.panelDetailRow}>
                <View style={styles.panelDetail}>
                  <Text style={styles.detailLabel}>Itens</Text>
                  <Text style={styles.detailValue}>{numAssets}</Text>
                </View>
                <View style={styles.panelDetail}>
                  <Text style={styles.detailLabel}>Investido</Text>
                  <Text style={styles.detailValue}>{formatMoney(assets?.summary?.total_invested || 0)}</Text>
                </View>
                <View style={styles.panelDetail}>
                  <Text style={styles.detailLabel}>Status</Text>
                  <Text style={[styles.detailValue, { color: '#FFD700' }]}>+{assets?.summary?.total_status_boost || 0}</Text>
                </View>
              </View>
            </>
          ) : (
            <View style={styles.panelEmpty}>
              <Text style={styles.panelEmptyText}>Nenhum bem adquirido</Text>
              <Text style={styles.panelEmptyHint}>Compre veículos, imóveis e itens de luxo</Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Ionicons name="school" size={24} color="#2196F3" />
            <Text style={styles.statValue}>{stats.education_count}</Text>
            <Text style={styles.statLabel}>Educação</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="ribbon" size={24} color="#FF9800" />
            <Text style={styles.statValue}>{stats.certification_count}</Text>
            <Text style={styles.statLabel}>Certificações</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="briefcase" size={24} color="#9C27B0" />
            <Text style={styles.statValue}>{stats.work_experience_count}</Text>
            <Text style={styles.statLabel}>Empregos</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="time" size={24} color="#F44336" />
            <Text style={styles.statValue}>{stats.months_experience}</Text>
            <Text style={styles.statLabel}>Meses Exp.</Text>
          </View>
        </View>

        {/* Skills */}
        <View style={styles.skillsCard}>
          <Text style={styles.sectionTitle}>Habilidades</Text>
          {Object.entries(stats.skills).map(([skill, level]: [string, any]) => (
            <View key={skill} style={styles.skillRow}>
              <Text style={styles.skillName}>{skill.charAt(0).toUpperCase() + skill.slice(1)}</Text>
              <View style={styles.skillBar}>
                <View style={[styles.skillFill, { width: `${level * 10}%` }]} />
              </View>
              <Text style={styles.skillLevel}>{level}/10</Text>
            </View>
          ))}
        </View>
      </ScrollView>
      <TutorialOverlay />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingText: {
    color: '#888',
    textAlign: 'center',
    marginTop: 12,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarImage: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  greeting: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  location: {
    fontSize: 13,
    color: '#888',
    marginTop: 2,
  },
  levelBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginLeft: 8,
  },
  levelText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  // Net Worth Card
  netWorthCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },
  netWorthHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  netWorthLabel: {
    color: '#888',
    fontSize: 14,
  },
  netWorthValue: {
    color: '#FFD700',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  netWorthBreakdown: {
    gap: 8,
  },
  breakdownItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  breakdownDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  breakdownLabel: {
    color: '#888',
    fontSize: 13,
    flex: 1,
  },
  breakdownValue: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  // Experience
  expCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  expHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  expLabel: {
    color: '#fff',
    fontSize: 15,
    fontWeight: 'bold',
  },
  expValue: {
    color: '#888',
    fontSize: 13,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#3a3a3a',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  // Panel Cards
  panelCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  panelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  panelTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  panelIconBg: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  panelTitle: {
    color: '#fff',
    fontSize: 17,
    fontWeight: 'bold',
  },
  panelMainRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  panelBigValue: {
    color: '#2196F3',
    fontSize: 22,
    fontWeight: 'bold',
  },
  panelSubLabel: {
    color: '#666',
    fontSize: 12,
    marginTop: 2,
  },
  profitBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  profitText: {
    fontSize: 13,
    fontWeight: 'bold',
  },
  panelDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  panelDetail: {
    alignItems: 'center',
    flex: 1,
  },
  detailLabel: {
    color: '#666',
    fontSize: 11,
    marginBottom: 4,
  },
  detailValue: {
    color: '#fff',
    fontSize: 13,
    fontWeight: 'bold',
  },
  panelEmpty: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  panelEmptyText: {
    color: '#666',
    fontSize: 14,
    fontWeight: '600',
  },
  panelEmptyHint: {
    color: '#555',
    fontSize: 12,
    marginTop: 4,
  },
  // Mini Holdings
  miniHolding: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  miniTicker: {
    color: '#ccc',
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
  },
  miniQty: {
    color: '#888',
    fontSize: 12,
    marginHorizontal: 12,
  },
  miniProfit: {
    fontSize: 13,
    fontWeight: 'bold',
  },
  miniIcon: {
    width: 22,
    height: 22,
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  seeMore: {
    color: '#555',
    fontSize: 12,
    textAlign: 'center',
    paddingTop: 8,
  },
  // Stats Grid
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 12,
  },
  statCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 14,
    flex: 1,
    minWidth: '46%',
    alignItems: 'center',
  },
  statValue: {
    color: '#fff',
    fontSize: 22,
    fontWeight: 'bold',
    marginTop: 6,
  },
  statLabel: {
    color: '#888',
    fontSize: 11,
    marginTop: 4,
  },
  // Skills
  skillsCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 17,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  skillRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  skillName: {
    color: '#fff',
    width: 110,
    fontSize: 13,
  },
  skillBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#3a3a3a',
    borderRadius: 3,
    marginHorizontal: 10,
    overflow: 'hidden',
  },
  skillFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  skillLevel: {
    color: '#888',
    width: 36,
    textAlign: 'right',
    fontSize: 13,
  },
});
