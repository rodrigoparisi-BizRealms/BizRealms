import { safeFixed } from '../../utils/safeFixed';
import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl,
  Alert, ActivityIndicator, Modal, TextInput, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { useSounds } from '../../hooks/useSounds';
import { useLanguage } from '../../context/LanguageContext';
import { SkeletonList } from '../../components/SkeletonLoader';
import { useHaptics } from '../../hooks/useHaptics';
import { useTheme } from '../../context/ThemeContext';

import { useAds } from '../../context/AdContext';
import { useSound } from '../../context/SoundContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const SEGMENT_LABELS: Record<string, string> = {
  restaurante: 'Restaurante', loja: 'Loja/Varejo', tecnologia: 'Tecnologia',
  fabrica: 'Fábrica', saude: 'Saúde', educacao: 'Educação',
  entretenimento: 'Entretenimento', imobiliaria: 'Imobiliária',
  logistica: 'Logística', agronegocio: 'Agronegócio',
};

export default function Companies() {
  const { token, user, refreshUser } = useAuth();
  const { colors } = useTheme();
  const { showAd } = useAds();
  const { playClick, playSuccess } = useSound();
  const [available, setAvailable] = useState<any[]>([]);
  const [owned, setOwned] = useState<any[]>([]);
  const [totalRevenue, setTotalRevenue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'owned' | 'buy' | 'create' | 'offers'>('owned');
  const [buying, setBuying] = useState<string | null>(null);
  const [collecting, setCollecting] = useState(false);
  const [watchingAd, setWatchingAd] = useState(false);
  const [adProgress, setAdProgress] = useState(0);
  // Create modal
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSegment, setNewSegment] = useState('restaurante');
  // Merge modal
  const [showMerge, setShowMerge] = useState(false);
  const [franchising, setFranchising] = useState<string | null>(null);
  // Offers
  const [offers, setOffers] = useState<any[]>([]);
  const [respondingOffer, setRespondingOffer] = useState<string | null>(null);
  const { play } = useSounds();
  const { trigger: haptic } = useHaptics();
  const { t, formatMoney } = useLanguage();

  const FRANCHISE_SEGMENTS = ['restaurante', 'loja', 'fabrica'];

  const handleCreateFranchise = async (company: any) => {
    const cost = Math.round(company.purchase_price * 0.6);
    const doIt = Platform.OS === 'web'
      ? window.confirm(`Criar franquia de "${company.name}"?\n\nCusto: $ ${cost.toLocaleString('en-US')}\nReceita: 70% da original`)
      : await new Promise<boolean>(resolve => Alert.alert(t('companies.createFranchise') || 'Create Franchise', `${t('companies.franchiseOf') || 'Create franchise of'} "${company.name}"?\n\n${t('general.cost') || 'Cost'}: $ ${cost.toLocaleString('en-US')}\n${t('companies.revenue') || 'Revenue'}: 70%`, [{ text: t('general.cancel'), onPress: () => resolve(false) }, { text: t('general.confirm'), onPress: () => resolve(true) }]));
    if (!doIt) return;
    setFranchising(company.id);
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/create-franchise`, { company_id: company.id }, { headers: { Authorization: `Bearer ${token}` } });
      if (Platform.OS === 'web') window.alert(`Franquia Criada!\n\n${r.data.message}`);
      else Alert.alert('Franquia Criada!', r.data.message);
      await loadData(); await refreshUser();
    } catch (e: any) {
      const msg = e.response?.data?.detail || t('general.error');
      if (Platform.OS === 'web') window.alert(msg);
      else Alert.alert(t('general.error'), msg);
    } finally { setFranchising(null); }
  };
  const handleSellCompany = (company: any) => {
    const sellPrice = Math.round(company.purchase_price * 0.8);
    const totalReturn = (company.total_collected || 0) + sellPrice;
    const profit = totalReturn - (company.purchase_price || 0);
    const roiText = profit >= 0 
      ? `\n\n✅ Retorno: +${formatMoney(profit)} (investimento recuperado!)`
      : `\n\n⚠️ Prejuízo: ${formatMoney(profit)} (investimento não recuperado)`;
    const franchiseWarning = !company.is_franchise ? '\n\nATENÇÃO: Todas as franquias desta empresa também serão vendidas!' : '';
    confirmAction(t('companies.sell') || 'Vender Empresa', `${t('companies.sellConfirm') || 'Deseja vender'} "${company.name}" ${t('companies.sellFor') || 'por'} ${formatMoney(sellPrice)}?${roiText}${franchiseWarning}`, async () => {
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/sell`, { company_id: company.id }, { headers: { Authorization: `Bearer ${token}` } });
        showAlert('Empresa Vendida!', r.data.message);
        play('sell');
        await loadData(); await refreshUser();
      } catch (e: any) {
        showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
      }
    });
  };

  const [mergeFrom, setMergeFrom] = useState<string | null>(null);
  const [mergeTo, setMergeTo] = useState<string | null>(null);

  const handleOfferRespond = (offerId: string, action: 'accept' | 'decline', buyerName: string, amount?: number, companyName?: string) => {
    if (action === 'accept') {
      confirmAction(
        'Aceitar Oferta',
        `${t('companies2.sellForTo')} "${companyName}" ${buyerName} $ ${(amount || 0).toLocaleString('en-US')}?\n\n${t('companies2.sellIrreversible')}`,
        async () => {
          setRespondingOffer(offerId);
          try {
            const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/offers/respond`, { offer_id: offerId, action: 'accept' }, { headers: { Authorization: `Bearer ${token}` } });
            showAlert('Venda Concluída!', r.data.message);
            play('sell');
            await loadData(); await refreshUser();
          } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
          finally { setRespondingOffer(null); }
        }
      );
    } else {
      setRespondingOffer(offerId);
      axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/offers/respond`, { offer_id: offerId, action: 'decline' }, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => { showAlert('Oferta Recusada', r.data.message); loadData(); })
        .catch(e => showAlert(t('general.error'), e.response?.data?.detail || t('general.error')))
        .finally(() => setRespondingOffer(null));
    }
  };

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [avRes, ownRes, offRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/available`, { headers: h }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/owned`, { headers: h }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/offers`, { headers: h }).catch(() => ({ data: { offers: [] } })),
      ]);
      setAvailable(avRes.data);
      setOwned(ownRes.data.companies);
      setTotalRevenue(ownRes.data.total_daily_revenue);
      setOffers(offRes.data.offers || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const onRefresh = async () => { setRefreshing(true); await loadData(); await refreshUser(); setRefreshing(false); };

  const showAlert = (title: string, msg: string) => {
    if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
    else Alert.alert(title, msg);
  };

  const confirmAction = (title: string, msg: string, onOk: () => void) => {
    if (Platform.OS === 'web') { if (window.confirm(`${title}\n\n${msg}`)) onOk(); }
    else Alert.alert(title, msg, [{ text: t('general.cancel'), style: 'cancel' }, { text: t('general.confirm'), onPress: onOk }]);
  };

  const handleBuy = (company: any) => {
    const roiMonths = (company.daily_revenue || 0) > 0 ? safeFixed((company.price || 0) / company.daily_revenue, 1) : '?';
    confirmAction(t('companies.buy') || 'Comprar Empresa', `${t('companies.buyConfirm') || 'Deseja comprar'} ${company.name} ${t('companies.buyFor') || 'por'} ${formatMoney(company.price)}?\n\n💵 ${t('companies.monthlyRevenue') || 'Receita diária'}: ${formatMoney(company.daily_revenue)}\n📊 ${t('companies.roiEstimate') || 'Retorno estimado'}: ${roiMonths} ${t('general.months') || 'meses'}`, async () => {
      setBuying(company.id);
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/buy`, { company_id: company.id }, { headers: { Authorization: `Bearer ${token}` } });
        showAlert('Compra Realizada!', r.data.message);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
      finally { setBuying(null); }
    });
  };

  const handleCollect = async () => {
    setCollecting(true);
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/collect-revenue`, {}, { headers: { Authorization: `Bearer ${token}` } });
      if (r.data.total_revenue > 0) {
        let msg = `Total: $ ${r.data.total_revenue.toLocaleString('en-US')}\nXP: +${r.data.xp_gained}`;
        r.data.details?.forEach((d: any) => { msg += `\n• ${d.name}: $ ${safeFixed(d.revenue, 2)}`; });
        showAlert('Receitas Coletadas!', msg);
      } else { showAlert('Aviso', r.data.message); }
      await loadData(); await refreshUser();
    } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
    finally { setCollecting(false); }
  };

  const handleAdBoost = () => {
    // Get current boost level
    const currentLevel = owned.length > 0 ? (owned[0].ad_boost_level || 1) : 1;
    const isActive = owned.some(c => c.ad_boost_active);
    const effectiveLevel = isActive ? currentLevel : 0;
    
    if (effectiveLevel >= 10) {
      showAlert('Boost Máximo!', 'Suas empresas já estão no boost máximo de 10x!');
      return;
    }
    
    // Show ad through AdContext, then call backend on reward
    showAd(async () => {
      await completeAdBoost();
    }, 'boost');
  };

  const completeAdBoost = async () => {
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/ad-boost`, {}, { headers: { Authorization: `Bearer ${token}` } });
      const level = r.data.boost_level || 1;
      showAlert(`Boost ${level}x Ativado!`, `${r.data.message}\n\n${r.data.companies_boosted} empresas no nível ${level}x!`);
      await loadData();
    } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
  };

  const handleCreate = async () => {
    if (!newName.trim()) { showAlert(t('general.error'), 'Digite o nome da empresa'); return; }
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/create`, { name: newName, segment: newSegment }, { headers: { Authorization: `Bearer ${token}` } });
      showAlert('Empresa Criada!', `${r.data.message}\nReceita estimada: $ ${r.data.company.daily_revenue}/dia`);
      setShowCreate(false); setNewName('');
      await loadData(); await refreshUser();
    } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
  };

  const handleMerge = async () => {
    if (!mergeFrom || !mergeTo) { showAlert(t('general.error'), 'Selecione duas empresas'); return; }
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/merge`, { company_id_1: mergeFrom, company_id_2: mergeTo }, { headers: { Authorization: `Bearer ${token}` } });
      showAlert('Fusão Concluída!', r.data.message);
      setShowMerge(false); setMergeFrom(null); setMergeTo(null);
      await loadData(); await refreshUser();
    } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
  };

  const hasBoostActive = owned.some(c => c.ad_boost_active);
  const currentBoostLevel = hasBoostActive ? (owned[0]?.ad_boost_level || 1) : 0;
  const isMaxBoost = currentBoostLevel >= 10;

  // Group franchises under their parent companies
  const groupedCompanies = React.useMemo(() => {
    const parents: any[] = [];
    const franchiseMap: Record<string, any[]> = {};

    // Separate parents and franchises
    owned.forEach(c => {
      if (c.is_franchise && c.parent_company_id) {
        if (!franchiseMap[c.parent_company_id]) franchiseMap[c.parent_company_id] = [];
        franchiseMap[c.parent_company_id].push(c);
      } else {
        parents.push(c);
      }
    });

    // Merge franchise data into parent cards
    return parents.map(p => {
      const franchises = franchiseMap[p.id] || [];
      const franchiseCount = franchises.length;
      const franchiseRevenue = franchises.reduce((sum: number, f: any) => sum + (f.effective_revenue || f.daily_revenue || 0), 0);
      const franchiseEmployees = franchises.reduce((sum: number, f: any) => sum + (f.employees || 0), 0);
      const franchiseCollected = franchises.reduce((sum: number, f: any) => sum + (f.total_collected || 0), 0);
      const franchiseInvestment = franchises.reduce((sum: number, f: any) => sum + (f.purchase_price || 0), 0);

      return {
        ...p,
        _franchiseCount: franchiseCount,
        _totalRevenue: (p.effective_revenue || 0) + franchiseRevenue,
        _totalEmployees: (p.employees || 0) + franchiseEmployees,
        _totalCollected: (p.total_collected || 0) + franchiseCollected,
        _totalInvestment: (p.purchase_price || 0) + franchiseInvestment,
      };
    });
  }, [owned]);

  // Count for display (parents only, since franchises are grouped)
  const parentCount = groupedCompanies.length;
  const totalUnits = owned.length;

  if (loading) return (<SafeAreaView style={[s.container, { backgroundColor: colors.background }]}><SkeletonList count={4} style={{ padding: 16 }} /></SafeAreaView>);

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={s.header}><Text style={s.title}>{t('companies.title')}</Text><Ionicons name="business" size={28} color="#4CAF50" /></View>
      {/* Mode Toggle */}
      <View style={s.toggle}>
        {(['owned', 'offers', 'buy', 'create'] as const).map(m => (
          <TouchableOpacity key={m} style={[s.toggleBtn, viewMode === m && s.toggleActive]} onPress={() => m === 'create' ? setShowCreate(true) : setViewMode(m)}>
            <Ionicons name={m === 'owned' ? 'business' : m === 'offers' ? 'mail' : m === 'buy' ? 'cart' : 'add-circle'} size={16} color={viewMode === m ? '#fff' : '#888'} />
            <Text style={[s.toggleText, viewMode === m && s.toggleTextActive]}>
              {m === 'owned' ? `${t('companies.mine')} (${parentCount}${totalUnits > parentCount ? `+${totalUnits - parentCount}` : ''})` : m === 'offers' ? `${t('companies.offers')}${offers.length > 0 ? ` (${offers.length})` : ''}` : m === 'buy' ? t('companies.buy') : t('companies.create')}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView contentContainerStyle={s.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />}>
        {/* OWNED VIEW */}
        {viewMode === 'owned' && (<>
          {owned.length > 0 && (
            <View style={s.revenueCard}>
              <Text style={s.revenueLabel}>{t('companies.revenue')}</Text>
              <Text style={s.revenueValue}>{formatMoney(totalRevenue)}/{t('general.month')}</Text>
              {hasBoostActive && (
                <View style={s.boostSection}>
                  <View style={s.boostBadge}>
                    <Ionicons name="flash" size={14} color="#000" />
                    <Text style={s.boostText}>{currentBoostLevel}x BOOST{isMaxBoost ? ' MAX' : ''}</Text>
                  </View>
                  {/* Progress bar showing boost level 1-10 */}
                  <View style={s.boostProgress}>
                    {[...Array(10)].map((_, i) => (
                      <View key={i} style={[s.boostDot, i < currentBoostLevel && s.boostDotActive, i === 9 && currentBoostLevel >= 10 && { backgroundColor: '#FF5722' }]} />
                    ))}
                  </View>
                  <Text style={s.boostProgressText}>{currentBoostLevel}/10</Text>
                </View>
              )}
              <View style={s.actionRow}>
                <TouchableOpacity style={[s.collectBtn, collecting && s.disabled]} onPress={handleCollect} disabled={collecting}>
                  <Ionicons name="cash" size={18} color="#fff" />
                  <Text style={s.collectText}>{collecting ? t('general.loading') : t('companies.collect')}</Text>
                </TouchableOpacity>
              </View>
              {!isMaxBoost ? (
                <TouchableOpacity style={s.adBtn} onPress={handleAdBoost}>
                  <Ionicons name="play-circle" size={18} color="#fff" />
                  <Text style={s.adText}>
                    {hasBoostActive
                      ? `Assistir anúncio (${currentBoostLevel}x → ${currentBoostLevel + 1}x)`
                      : 'Assistir anúncio (+2x boost)'}
                  </Text>
                </TouchableOpacity>
              ) : (
                <View style={[s.adBtn, { backgroundColor: '#333', opacity: 0.6 }]}>
                  <Ionicons name="checkmark-circle" size={18} color="#4CAF50" />
                  <Text style={s.adText}>Boost Máximo 10x Ativado!</Text>
                </View>
              )}
              {owned.length >= 2 && (
                <TouchableOpacity style={s.mergeBtn} onPress={() => setShowMerge(true)}>
                  <Ionicons name="git-merge" size={18} color="#2196F3" />
                  <Text style={s.mergeText}>{t('companies.merge')} (+30%)</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
          {owned.length === 0 ? (
            <View style={s.empty}><Ionicons name="business-outline" size={64} color="#555" /><Text style={s.emptyTitle}>{t('companies.noCompanies')}</Text><Text style={s.emptySub}>{t('companies.buyFirst')}</Text>
              <TouchableOpacity style={s.goBtn} onPress={() => setViewMode('buy')}><Text style={s.goBtnText}>{t('companies.buy')}</Text></TouchableOpacity></View>
          ) : groupedCompanies.map(c => (
            <View key={c.id} style={[s.companyCard, { borderLeftColor: c.color, borderLeftWidth: 4 }]}>
              <View style={s.companyHeader}>
                <View style={[s.companyIcon, { backgroundColor: c.color }]}>
                  <Ionicons name={c.icon as any} size={20} color="#fff" />
                  {c._franchiseCount > 0 && (
                    <View style={s.franchiseCountBadge}>
                      <Text style={s.franchiseCountText}>{1 + c._franchiseCount}</Text>
                    </View>
                  )}
                </View>
                <View style={s.companyInfo}>
                  <Text style={s.companyName}>{c.name}</Text>
                  <Text style={s.companySegment}>
                    {SEGMENT_LABELS[c.segment] || c.segment} • {t('profile.levelLabel')} {c.level || 1}
                    {c._franchiseCount > 0 ? ` • ${c._franchiseCount} ${c._franchiseCount === 1 ? (t('companies.franchiseSingular') || 'franquia') : (t('companies.franchisePlural') || 'franquias')}` : ''}
                  </Text>
                </View>
                <View style={s.companyRevenue}>
                  <Text style={s.revText}>{formatMoney(c._totalRevenue)}</Text>
                  <Text style={s.revLabel}>/dia</Text>
                  {c.ad_boost_active && <Text style={s.boostMini}>{c.ad_boost_level || 1}x!</Text>}
                </View>
              </View>
              <Text style={s.companyDesc}>{c.description}</Text>
              <View style={s.companyMeta}>
                <Text style={s.metaText}>👥 {c._totalEmployees} emp.</Text>
                <Text style={s.metaText}>💰 Total: {formatMoney(c._totalCollected)}</Text>
                <Text style={s.metaText}>📊 ROI: {c.roi_months || '?'}m</Text>
              </View>
              {/* ROI Progress */}
              <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 8 }}>
                <View style={{ flex: 1, height: 6, backgroundColor: '#333', borderRadius: 3, overflow: 'hidden' }}>
                  <View style={{ width: `${Math.min(c.roi_progress || 0, 100)}%`, height: '100%', backgroundColor: (c.roi_recovered) ? '#4CAF50' : '#FF9800', borderRadius: 3 }} />
                </View>
                <Text style={{ color: (c.roi_recovered) ? '#4CAF50' : '#FF9800', fontSize: 11, fontWeight: 'bold', minWidth: 40 }}>
                  {c.roi_recovered ? '✅' : `${Math.round(c.roi_progress || 0)}%`}
                </Text>
              </View>
              {/* Franchise summary */}
              {c._franchiseCount > 0 && (
                <View style={s.franchiseSummary}>
                  <Ionicons name="git-branch" size={14} color="#9C27B0" />
                  <Text style={s.franchiseSummaryText}>
                    {c._franchiseCount} {c._franchiseCount === 1 ? (t('companies.franchiseSingular') || 'franquia') : (t('companies.franchisePlural') || 'franquias')} • {t('companies.invested') || 'Investido'}: {formatMoney(c._totalInvestment)}
                  </Text>
                </View>
              )}
              {!c.is_franchise && FRANCHISE_SEGMENTS.includes(c.segment) && (
                <TouchableOpacity style={[s.franchiseBtn, franchising === c.id && s.disabled]} onPress={() => handleCreateFranchise(c)} disabled={franchising === c.id}>
                  <Ionicons name="git-branch" size={16} color="#9C27B0" />
                  <Text style={s.franchiseBtnText}>{franchising === c.id ? t('general.loading') : `${t('companies.createFranchise')} (60%, 70%)`}</Text>
                </TouchableOpacity>
              )}
              {/* Sell Button */}
              <TouchableOpacity style={s.sellBtn} onPress={() => handleSellCompany(c)}>
                <Ionicons name="cash-outline" size={16} color="#F44336" />
                <Text style={s.sellBtnText}>{t('companies.sell')} {formatMoney(Math.round((c.purchase_price || 0) * 0.8))}</Text>
              </TouchableOpacity>
            </View>
          ))}
        </>)}

        {/* OFFERS VIEW */}
        {viewMode === 'offers' && (<>
          {/* Ad-gated offer controls */}
          <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
            <TouchableOpacity
              style={{ flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: '#FF980020', borderRadius: 12, paddingVertical: 12, borderWidth: 1, borderColor: '#FF980040' }}
              onPress={() => { playClick(); showAd(() => { onRefresh(); }, 'offer'); }}
            >
              <Ionicons name="add-circle" size={18} color="#FF9800" />
              <Text style={{ color: '#FF9800', fontSize: 13, fontWeight: '600' }}>{t('companies.newOffersAd') || 'Novas Ofertas'}</Text>
              <Ionicons name="play-circle" size={14} color="#FF980080" />
            </TouchableOpacity>
          </View>

          {offers.length === 0 ? (
            <View style={s.empty}>
              <Ionicons name="mail-outline" size={64} color="#555" />
              <Text style={s.emptyTitle}>{t('companies.noOffers')}</Text>
              <Text style={s.emptySub}>Novas ofertas surgem periodicamente para suas empresas. Volte mais tarde!</Text>
              <TouchableOpacity style={s.goBtn} onPress={() => { onRefresh(); }}>
                <Text style={s.goBtnText}>{t('companies.checkOffers')}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <View style={s.offersHeader}>
                <Ionicons name="mail-unread" size={20} color="#FF9800" />
                <Text style={s.offersHeaderText}>{offers.length} oferta(s) ativa(s)</Text>
              </View>
              {offers.map((offer: any) => {
                const isGoodDeal = offer.multiplier >= 1.0;
                const profitPercent = Math.round((offer.multiplier - 1) * 100);
                const profitAmount = offer.offer_amount - offer.purchase_price;
                const remainHours = Math.floor((offer.remaining_minutes || 0) / 60);
                const remainMins = (offer.remaining_minutes || 0) % 60;

                return (
                  <View key={offer.id} style={[s.offerCard, { borderLeftColor: isGoodDeal ? '#4CAF50' : '#F44336', borderLeftWidth: 4 }]}>
                    {/* Offer Header */}
                    <View style={s.offerHeader}>
                      <View style={[s.offerTypeBadge, { backgroundColor: offer.reason_type === 'high' ? '#4CAF5020' : offer.reason_type === 'low' ? '#F4433620' : '#FF980020' }]}>
                        <Text style={s.offerEmoji}>{offer.reason_emoji || '📋'}</Text>
                        <Text style={[s.offerTypeText, { color: offer.reason_type === 'high' ? '#4CAF50' : offer.reason_type === 'low' ? '#F44336' : '#FF9800' }]}>
                          {offer.reason_type === 'high' ? t('companies.goodOffer') : offer.reason_type === 'low' ? t('companies.lowOffer') : t('companies.neutralOffer')}
                        </Text>
                      </View>
                      <View style={s.offerTimer}>
                        <Ionicons name="time" size={14} color="#888" />
                        <Text style={s.offerTimerText}>
                          {remainHours > 0 ? `${remainHours}h ${remainMins}m` : `${remainMins}m`}
                        </Text>
                      </View>
                    </View>

                    {/* Buyer & Company */}
                    <Text style={s.offerBuyer}>{offer.buyer_name}</Text>
                    <Text style={s.offerReason}>{offer.reason}</Text>
                    <View style={s.offerCompanyRow}>
                      <Ionicons name="business" size={14} color="#888" />
                      <Text style={s.offerCompanyName}>{offer.company_name}</Text>
                      <Text style={s.offerSegment}>{SEGMENT_LABELS[offer.company_segment] || offer.company_segment}</Text>
                    </View>

                    {/* Price comparison */}
                    <View style={s.offerPriceBlock}>
                      <View style={s.offerPriceItem}>
                        <Text style={s.offerPriceLabel}>{t('companies.youPaid')}</Text>
                        <Text style={s.offerPriceOld}>$ {(offer.purchase_price || 0).toLocaleString('en-US')}</Text>
                      </View>
                      <View style={s.offerArrow}>
                        <Ionicons name="arrow-forward" size={20} color="#888" />
                      </View>
                      <View style={s.offerPriceItem}>
                        <Text style={s.offerPriceLabel}>{t('companies.offer')}</Text>
                        <Text style={[s.offerPriceNew, { color: isGoodDeal ? '#4CAF50' : '#F44336' }]}>
                          $ {(offer.offer_amount || 0).toLocaleString('en-US')}
                        </Text>
                      </View>
                    </View>

                    {/* Profit/Loss indicator */}
                    <View style={[s.offerProfitBadge, { backgroundColor: isGoodDeal ? '#4CAF5015' : '#F4433615' }]}>
                      <Ionicons name={isGoodDeal ? 'trending-up' : 'trending-down'} size={16} color={isGoodDeal ? '#4CAF50' : '#F44336'} />
                      <Text style={[s.offerProfitText, { color: isGoodDeal ? '#4CAF50' : '#F44336' }]}>
                        {isGoodDeal ? '+' : ''}{profitPercent}% ({profitAmount >= 0 ? '+' : ''}$ {profitAmount.toLocaleString('en-US')})
                      </Text>
                    </View>

                    {/* Better Offer via Ad */}
                    {!offer.ad_improved && (
                    <TouchableOpacity
                      style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: '#9C27B010', borderRadius: 8, paddingVertical: 8, marginBottom: 8, borderWidth: 1, borderColor: '#9C27B030' }}
                      onPress={() => showAd(async () => {
                        try {
                          const res = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/companies/offers/improve`, { offer_id: offer.id }, { headers: { Authorization: `Bearer ${token}` } });
                          if (res.data?.success) {
                            setOffers(prev => prev.map(o => o.id === offer.id ? { ...o, offer_amount: res.data.new_amount, multiplier: res.data.multiplier, ad_improved: true } : o));
                            if (Platform.OS === 'web') window.alert(res.data.message);
                            else Alert.alert(t('general.success') || 'Success', res.data.message);
                          }
                        } catch (e: any) {
                          const msg = e.response?.data?.detail || t('general.error') || 'Error';
                          if (Platform.OS === 'web') window.alert(msg);
                          else Alert.alert(t('general.error') || 'Error', msg);
                        }
                      }, 'better_offer')}
                    >
                      <Ionicons name="trending-up" size={16} color="#9C27B0" />
                      <Text style={{ color: '#9C27B0', fontSize: 12, fontWeight: '600' }}>{t('companies.betterOfferAd') || 'Better Offer'}</Text>
                      <Ionicons name="play-circle" size={14} color="#9C27B060" />
                    </TouchableOpacity>
                    )}

                    {/* Actions */}
                    <View style={s.offerActions}>
                      <TouchableOpacity
                        style={[s.offerDeclineBtn, respondingOffer === offer.id && s.disabled]}
                        disabled={respondingOffer === offer.id}
                        onPress={() => handleOfferRespond(offer.id, 'decline', offer.buyer_name)}
                      >
                        <Ionicons name="close-circle" size={18} color="#F44336" />
                        <Text style={s.offerDeclineText}>{t('companies.decline')}</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[s.offerAcceptBtn, respondingOffer === offer.id && s.disabled]}
                        disabled={respondingOffer === offer.id}
                        onPress={() => handleOfferRespond(offer.id, 'accept', offer.buyer_name, offer.offer_amount, offer.company_name)}
                      >
                        {respondingOffer === offer.id ? <ActivityIndicator size="small" color="#fff" /> : (
                          <>
                            <Ionicons name="checkmark-circle" size={18} color="#fff" />
                            <Text style={s.offerAcceptText}>{t('companies.acceptOffer')}</Text>
                          </>
                        )}
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })}
            </>
          )}
        </>)}

        {/* BUY VIEW */}
        {viewMode === 'buy' && (<>
          {available.length === 0 ? (
            <View style={s.empty}>
              <Ionicons name="cart-outline" size={64} color="#555" />
              <Text style={s.emptyTitle}>{t('companies.noAvailable') || 'No companies available'}</Text>
              <Text style={s.emptySub}>{t('companies.checkLater') || 'Check back later for new companies!'}</Text>
            </View>
          ) : available.map(c => {
          const canAfford = (user?.money || 0) >= c.price;
          const hasLevel = (user?.level || 1) >= c.level_required;
          return (
            <View key={c.id} style={[s.buyCard, c.already_owned && s.ownedCard]}>
              <View style={s.buyHeader}>
                <View style={[s.companyIcon, { backgroundColor: c.color }]}><Ionicons name={c.icon as any} size={20} color="#fff" /></View>
                <View style={s.buyInfo}>
                  <Text style={s.buyName}>{c.name}</Text>
                  <Text style={s.buySegment}>{SEGMENT_LABELS[c.segment]}</Text>
                </View>
                <Text style={s.buyPrice}>{formatMoney(c.price)}</Text>
              </View>
              <Text style={s.buyDesc}>{c.description}</Text>
              <View style={s.buyMeta}>
                <Text style={s.metaText}>💵 {formatMoney(c.daily_revenue || 0)}/day</Text>
                <Text style={s.metaText}>👥 {c.employees || 0} emp.</Text>
                <Text style={s.metaText}>📊 ROI: {(c.daily_revenue || 0) > 0 ? safeFixed((c.price || 0) / c.daily_revenue, 0) : '?'}d</Text>
                <Text style={s.metaText}>📊 {t('profile.levelLabel')} {c.level_required || 1}</Text>
              </View>
              {c.already_owned ? (
                <View style={s.ownedBadge}><Ionicons name="checkmark-circle" size={16} color="#4CAF50" /><Text style={s.ownedText}>Já possui</Text></View>
              ) : (
                <TouchableOpacity style={[s.buyBtn, (!canAfford || !hasLevel) && s.disabled]} onPress={() => handleBuy(c)} disabled={buying === c.id}>
                  {buying === c.id ? <ActivityIndicator size="small" color="#fff" /> : (
                    <Text style={s.buyBtnText}>{!hasLevel ? `${t('jobs.levelRequired')} ${c.level_required}` : !canAfford ? t('bank.insufficient') : t('companies.buy')}</Text>
                  )}
                </TouchableOpacity>
              )}
            </View>
          );
        })}
        </>)}
      </ScrollView>

      {/* Create Modal */}
      <Modal visible={showCreate} animationType="slide" transparent onRequestClose={() => setShowCreate(false)}>
        <View style={s.modalOverlay}><View style={s.modal}>
          <View style={s.modalHeader}><Text style={s.modalTitle}>{t('companies.createCompany')}</Text><TouchableOpacity onPress={() => setShowCreate(false)}><Ionicons name="close" size={28} color="#fff" /></TouchableOpacity></View>
          <Text style={s.modalCost}>Custo de criação: $ 5.000</Text>
          <Text style={s.label}>{t('companies.companyName')}</Text>
          <TextInput style={s.input} placeholder="Ex: Minha Startup Tech" placeholderTextColor="#555" value={newName} onChangeText={setNewName} />
          <Text style={s.label}>{t('companies.segment')}</Text>
          <View style={s.segGrid}>
            {Object.entries(SEGMENT_LABELS).map(([key, label]) => (
              <TouchableOpacity key={key} style={[s.segChip, newSegment === key && s.segActive]} onPress={() => setNewSegment(key)}>
                <Text style={[s.segText, newSegment === key && s.segTextActive]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <TouchableOpacity style={s.createBtn} onPress={handleCreate}><Text style={s.createText}>{t('companies2.createCompanyBtn')}</Text></TouchableOpacity>
        </View></View>
      </Modal>

      {/* Merge Modal */}
      <Modal visible={showMerge} animationType="slide" transparent onRequestClose={() => setShowMerge(false)}>
        <View style={s.modalOverlay}><View style={s.modal}>
          <View style={s.modalHeader}><Text style={s.modalTitle}>{t('companies.merge')}</Text><TouchableOpacity onPress={() => setShowMerge(false)}><Ionicons name="close" size={28} color="#fff" /></TouchableOpacity></View>
          <Text style={s.modalCost}>{t('companies2.mergeHint')}</Text>
          <Text style={s.label}>{t('companies.title')}</Text>
          {owned.filter(c => !c.is_franchise).map(c => (
            <TouchableOpacity key={`m1-${c.id}`} style={[s.mergeOption, mergeFrom === c.id && s.mergeSelected]} onPress={() => setMergeFrom(c.id)}>
              <Text style={s.mergeOptionText}>{c.name} ({SEGMENT_LABELS[c.segment]})</Text>
            </TouchableOpacity>
          ))}
          <Text style={[s.label, { marginTop: 16 }]}>{t('companies2.mergeTarget')}</Text>
          {owned.filter(c => !c.is_franchise && c.id !== mergeFrom && (!mergeFrom || c.segment === owned.find(o => o.id === mergeFrom)?.segment)).map(c => (
            <TouchableOpacity key={`m2-${c.id}`} style={[s.mergeOption, mergeTo === c.id && s.mergeSelected]} onPress={() => setMergeTo(c.id)}>
              <Text style={s.mergeOptionText}>{c.name} ({SEGMENT_LABELS[c.segment]})</Text>
            </TouchableOpacity>
          ))}
          {mergeFrom && owned.filter(c => c.id !== mergeFrom && c.segment === owned.find(o => o.id === mergeFrom)?.segment).length === 0 && (
            <View style={{ paddingVertical: 12, alignItems: 'center' }}>
              <Text style={{ color: '#FF9800', fontSize: 13 }}>Nenhuma empresa do mesmo segmento disponível para fusão</Text>
            </View>
          )}
          <TouchableOpacity style={[s.createBtn, { backgroundColor: '#2196F3' }]} onPress={handleMerge}><Text style={s.createText}>{t('general.confirm')}</Text></TouchableOpacity>
        </View></View>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadingText: { color: '#888', fontSize: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#fff' },
  content: { padding: 16, paddingBottom: 32 },
  toggle: { flexDirection: 'row', margin: 16, marginBottom: 0, gap: 8 },
  toggleBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderRadius: 10, backgroundColor: '#2a2a2a', gap: 4 },
  toggleActive: { backgroundColor: '#4CAF50' },
  toggleText: { color: '#888', fontSize: 12, fontWeight: 'bold' },
  toggleTextActive: { color: '#fff' },
  // Revenue Card
  revenueCard: { backgroundColor: '#2a3a2a', borderRadius: 16, padding: 20, marginBottom: 20, borderWidth: 2, borderColor: '#4CAF50' },
  revenueLabel: { color: '#888', fontSize: 14 },
  revenueValue: { color: '#4CAF50', fontSize: 28, fontWeight: 'bold', marginVertical: 8 },
  boostBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFD700', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 4, alignSelf: 'flex-start', gap: 4 },
  boostText: { color: '#000', fontSize: 12, fontWeight: 'bold' },
  boostMini: { color: '#FFD700', fontSize: 11, fontWeight: 'bold' },
  boostSection: { marginBottom: 12, gap: 6 },
  boostProgress: { flexDirection: 'row', gap: 4, alignItems: 'center' },
  boostDot: { flex: 1, height: 6, borderRadius: 3, backgroundColor: '#3a3a3a' },
  boostDotActive: { backgroundColor: '#FFD700' },
  boostProgressText: { color: '#FFD700', fontSize: 11, fontWeight: 'bold', textAlign: 'right' },
  actionRow: { marginBottom: 8 },
  collectBtn: { backgroundColor: '#4CAF50', borderRadius: 12, padding: 14, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  collectText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  adBtn: { backgroundColor: '#FF6B6B', borderRadius: 12, padding: 14, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 8 },
  adText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  adWatching: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 8 },
  adWatchingText: { color: '#fff', fontSize: 14, marginBottom: 8 },
  progressBg: { width: '100%', height: 6, backgroundColor: '#3a3a3a', borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#FF6B6B' },
  mergeBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 8, backgroundColor: '#1a2a3a', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#2196F3' },
  mergeText: { color: '#2196F3', fontSize: 14, fontWeight: 'bold' },
  disabled: { opacity: 0.5 },
  // Company Card
  companyCard: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, marginBottom: 12 },
  companyHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  companyIcon: { width: 40, height: 40, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  companyInfo: { flex: 1 },
  companyName: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  companySegment: { color: '#888', fontSize: 12 },
  companyRevenue: { alignItems: 'flex-end' },
  revText: { color: '#4CAF50', fontSize: 16, fontWeight: 'bold' },
  revLabel: { color: '#666', fontSize: 10 },
  companyDesc: { color: '#888', fontSize: 12, marginBottom: 8 },
  companyMeta: { flexDirection: 'row', gap: 16 },
  metaText: { color: '#666', fontSize: 11 },
  // Buy Card
  buyCard: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, marginBottom: 12 },
  ownedCard: { opacity: 0.6 },
  buyHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  buyInfo: { flex: 1 },
  buyName: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  buySegment: { color: '#888', fontSize: 12 },
  buyPrice: { color: '#FFD700', fontSize: 16, fontWeight: 'bold' },
  buyDesc: { color: '#888', fontSize: 12, marginBottom: 8 },
  buyMeta: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  buyBtn: { backgroundColor: '#4CAF50', borderRadius: 10, padding: 12, alignItems: 'center' },
  buyBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  ownedBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'center', padding: 10 },
  ownedText: { color: '#4CAF50', fontWeight: 'bold' },
  // Empty
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyTitle: { color: '#fff', fontSize: 22, fontWeight: 'bold', marginTop: 16 },
  emptySub: { color: '#666', fontSize: 14, textAlign: 'center', marginTop: 8, maxWidth: 280 },
  goBtn: { backgroundColor: '#4CAF50', borderRadius: 12, paddingHorizontal: 24, paddingVertical: 12, marginTop: 20 },
  goBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  // Modals
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'flex-end' },
  modal: { backgroundColor: '#1a1a1a', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, maxHeight: '85%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modalTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  modalCost: { color: '#FF9800', fontSize: 14, marginBottom: 16 },
  label: { color: '#888', fontSize: 14, marginBottom: 8, marginTop: 12 },
  input: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, color: '#fff', fontSize: 16, borderWidth: 1, borderColor: '#3a3a3a' },
  segGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  segChip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: '#2a2a2a', borderWidth: 1, borderColor: '#3a3a3a' },
  segActive: { backgroundColor: '#4CAF50', borderColor: '#4CAF50' },
  segText: { color: '#888', fontSize: 12, fontWeight: 'bold' },
  segTextActive: { color: '#fff' },
  createBtn: { backgroundColor: '#4CAF50', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  createText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  mergeOption: { backgroundColor: '#2a2a2a', borderRadius: 10, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#3a3a3a' },
  mergeSelected: { borderColor: '#2196F3', backgroundColor: '#1a2a3a' },
  mergeOptionText: { color: '#fff', fontSize: 14 },
  franchiseBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8, backgroundColor: '#9C27B015', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  franchiseBadgeText: { color: '#9C27B0', fontSize: 12, fontWeight: '600' },
  franchiseCountBadge: { position: 'absolute', top: -6, right: -6, backgroundColor: '#9C27B0', borderRadius: 10, minWidth: 20, height: 20, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 4, borderWidth: 2, borderColor: '#2a2a2a' },
  franchiseCountText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  franchiseSummary: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8, backgroundColor: '#9C27B012', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, borderWidth: 1, borderColor: '#9C27B030' },
  franchiseSummaryText: { color: '#9C27B0', fontSize: 12, fontWeight: '600' },
  franchiseBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 10, borderWidth: 1, borderColor: '#9C27B0', backgroundColor: '#9C27B010' },
  franchiseBtnText: { color: '#9C27B0', fontSize: 12, fontWeight: 'bold' },
  sellBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 10, borderWidth: 1, borderColor: '#F44336', backgroundColor: '#F4433610' },
  sellBtnText: { color: '#F44336', fontSize: 12, fontWeight: 'bold' },
  // Offers
  offersHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16, backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#FF980040' },
  offersHeaderText: { color: '#FF9800', fontSize: 16, fontWeight: 'bold' },
  offerCard: { backgroundColor: '#2a2a2a', borderRadius: 14, padding: 16, marginBottom: 14 },
  offerHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  offerTypeBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  offerEmoji: { fontSize: 14 },
  offerTypeText: { fontSize: 12, fontWeight: 'bold' },
  offerTimer: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  offerTimerText: { color: '#888', fontSize: 12 },
  offerBuyer: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  offerReason: { color: '#aaa', fontSize: 13, marginTop: 2, marginBottom: 8 },
  offerCompanyRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 12 },
  offerCompanyName: { color: '#ccc', fontSize: 13, fontWeight: '600' },
  offerSegment: { color: '#888', fontSize: 12 },
  offerPriceBlock: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#1a1a1a', borderRadius: 12, padding: 14, marginBottom: 10 },
  offerPriceItem: { flex: 1, alignItems: 'center' },
  offerArrow: { paddingHorizontal: 12 },
  offerPriceLabel: { color: '#666', fontSize: 11, marginBottom: 4 },
  offerPriceOld: { color: '#888', fontSize: 15, fontWeight: '600' },
  offerPriceNew: { fontSize: 18, fontWeight: 'bold' },
  offerProfitBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, borderRadius: 10, padding: 10, marginBottom: 12 },
  offerProfitText: { fontSize: 14, fontWeight: 'bold' },
  offerActions: { flexDirection: 'row', gap: 10 },
  offerDeclineBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: '#1a1a1a', borderRadius: 10, padding: 12, borderWidth: 1, borderColor: '#F4433640' },
  offerDeclineText: { color: '#F44336', fontSize: 14, fontWeight: 'bold' },
  offerAcceptBtn: { flex: 2, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: '#4CAF50', borderRadius: 10, padding: 12 },
  offerAcceptText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
});
