import { safeFixed } from '../../utils/safeFixed';
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl,
  Alert, ActivityIndicator, Platform, Modal, Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useLanguage } from '../../context/LanguageContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function Patrimonio() {
  const { token, user, refreshUser } = useAuth();
  const { colors } = useTheme();
  const { t, formatMoney } = useLanguage();
  const [store, setStore] = useState<any[]>([]);
  const [owned, setOwned] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'owned' | 'store' | 'offers'>('owned');
  const [filterCat, setFilterCat] = useState('all');
  const [buying, setBuying] = useState<string | null>(null);
  const [offers, setOffers] = useState<any[]>([]);
  const [respondingOffer, setRespondingOffer] = useState<string | null>(null);

  const CATEGORY_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
    veiculo: { label: t('assets.categories.veiculo'), icon: 'car-sport', color: '#2196F3' },
    imovel: { label: t('assets.categories.imovel'), icon: 'home', color: '#FF9800' },
    luxo: { label: t('assets.categories.luxo'), icon: 'diamond', color: '#9C27B0' },
  };

  useEffect(() => { if (token) loadData(); }, [token]);

  const loadData = async () => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [storeRes, ownedRes, offersRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/store`, { headers: h }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/owned`, { headers: h }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/offers`, { headers: h }).catch(() => null),
      ]);
      setStore(storeRes.data);
      setOwned(ownedRes.data.assets);
      setSummary(ownedRes.data.summary);
      if (offersRes) setOffers(offersRes.data.offers || []);
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

  const handleBuy = (asset: any) => {
    confirmAction(t('assets.buyConfirm'), `${t('assets.buyQuestion')} ${asset.name} ${t('assets.forPrice')} ${formatMoney(asset.price)}?\n\n${asset.description}\n\n${t('assets.appreciationRate')}: ${asset.appreciation > 0 ? '+' : ''}${safeFixed((asset.appreciation || 0) * 100, 0)}%/${t('general.month')}`, async () => {
      setBuying(asset.id);
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/buy`, { asset_id: asset.id }, { headers: { Authorization: `Bearer ${token}` } });
        showAlert(t('assets.purchaseComplete'), `${r.data.message}\n${t('assets.statusBoost')}: +${r.data.status_boost}`);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
      finally { setBuying(null); }
    });
  };

  const handleSell = (asset: any) => {
    const profitLabel = asset.profit >= 0 ? `${t('assets.profit')}: ${formatMoney(asset.profit)}` : `${t('assets.loss')}: ${formatMoney(Math.abs(asset.profit))}`;
    confirmAction(t('assets.sellConfirm'), `${t('assets.sellQuestion')} ${asset.name}?\n\n${t('assets.currentValue')}: ${formatMoney(asset.current_value)}\n${profitLabel}`, async () => {
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/sell`, { asset_id: asset.id }, { headers: { Authorization: `Bearer ${token}` } });
        showAlert(t('assets.saleComplete'), r.data.message);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
    });
  };

  const handleOfferRespond = (offer: any, action: 'accept' | 'decline') => {
    const msg = action === 'accept'
      ? `${t('assets.acceptOffer')}: ${offer.buyer_name} - ${formatMoney(offer.offer_amount)} "${offer.asset_name}"?`
      : `${t('assets.declineOffer')}: ${offer.buyer_name}?`;
    confirmAction(action === 'accept' ? t('assets.acceptOffer') : t('assets.declineOffer'), msg, async () => {
      setRespondingOffer(offer.id);
      try {
        const r = await axios.post(
          `${EXPO_PUBLIC_BACKEND_URL}/api/assets/offers/respond`,
          { offer_id: offer.id, action },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        showAlert(action === 'accept' ? t('general.success') : t('general.success'), r.data.message);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert(t('general.error'), e.response?.data?.detail || t('general.error')); }
      finally { setRespondingOffer(null); }
    });
  };

  const filtered = filterCat === 'all' ? (viewMode === 'store' ? store : owned) : (viewMode === 'store' ? store : owned).filter(a => a.category === filterCat);

  if (loading) return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={s.center}>
        <ActivityIndicator size="large" color="#9C27B0" />
        <Text style={[s.loadText, { color: colors.textSecondary }]}>{t('assets.loading')}</Text>
      </View>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={[s.header, { borderBottomColor: colors.border }]}>
        <Text style={[s.title, { color: colors.text }]}>{t('assets.title')}</Text>
        <Ionicons name="diamond" size={28} color="#9C27B0" />
      </View>

      {/* Mode Toggle */}
      <View style={s.toggle}>
        <TouchableOpacity style={[s.tBtn, { backgroundColor: colors.card }, viewMode === 'owned' && s.tActive]} onPress={() => setViewMode('owned')}>
          <Ionicons name="wallet" size={16} color={viewMode === 'owned' ? '#fff' : colors.textSecondary} />
          <Text style={[s.tText, { color: colors.textSecondary }, viewMode === 'owned' && s.tTextActive]}>{t('assets.owned')} ({owned.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[s.tBtn, { backgroundColor: colors.card }, viewMode === 'offers' && { backgroundColor: '#FF9800' }]} onPress={() => setViewMode('offers')}>
          <Ionicons name="pricetag" size={16} color={viewMode === 'offers' ? '#fff' : colors.textSecondary} />
          <Text style={[s.tText, { color: colors.textSecondary }, viewMode === 'offers' && s.tTextActive]}>{t('assets.offers')} {offers.length > 0 ? `(${offers.length})` : ''}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[s.tBtn, { backgroundColor: colors.card }, viewMode === 'store' && s.tActive]} onPress={() => setViewMode('store')}>
          <Ionicons name="cart" size={16} color={viewMode === 'store' ? '#fff' : colors.textSecondary} />
          <Text style={[s.tText, { color: colors.textSecondary }, viewMode === 'store' && s.tTextActive]}>{t('assets.store')}</Text>
        </TouchableOpacity>
      </View>

      {/* Category Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.filterScroll}>
        <View style={s.filterRow}>
          <TouchableOpacity style={[s.fChip, { backgroundColor: colors.card }, filterCat === 'all' && s.fActive]} onPress={() => setFilterCat('all')}>
            <Text style={[s.fText, { color: colors.textSecondary }, filterCat === 'all' && s.fTextActive]}>{t('assets.categories.all')}</Text>
          </TouchableOpacity>
          {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => (
            <TouchableOpacity key={key} style={[s.fChip, { backgroundColor: colors.card }, filterCat === key && { backgroundColor: cfg.color }]} onPress={() => setFilterCat(key)}>
              <Ionicons name={cfg.icon as any} size={14} color={filterCat === key ? '#fff' : colors.textSecondary} />
              <Text style={[s.fText, { color: colors.textSecondary }, filterCat === key && s.fTextActive]}>{cfg.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <ScrollView contentContainerStyle={s.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#9C27B0" />}>
        {/* Portfolio Summary */}
        {viewMode === 'owned' && summary && summary.count > 0 && (
          <View style={[s.summaryCard, { backgroundColor: colors.card }]}>
            <Text style={[s.sumLabel, { color: colors.textSecondary }]}>{t('assets.totalPortfolioValue')}</Text>
            <Text style={[s.sumValue, { color: colors.text }]}>{formatMoney(summary.total_value)}</Text>
            <View style={s.sumRow}>
              <View style={s.sumItem}>
                <Text style={[s.sumItemLabel, { color: colors.textSecondary }]}>{t('assets.invested')}</Text>
                <Text style={[s.sumItemVal, { color: colors.text }]}>{formatMoney(summary.total_invested)}</Text>
              </View>
              <View style={s.sumItem}>
                <Text style={[s.sumItemLabel, { color: colors.textSecondary }]}>{t('assets.profitLoss')}</Text>
                <Text style={[s.sumItemVal, { color: summary.total_profit >= 0 ? '#4CAF50' : '#F44336' }]}>
                  {summary.total_profit >= 0 ? '+' : ''}{formatMoney(summary.total_profit)}
                </Text>
              </View>
              <View style={s.sumItem}>
                <Text style={[s.sumItemLabel, { color: colors.textSecondary }]}>{t('assets.statusBoost')}</Text>
                <Text style={[s.sumItemVal, { color: '#FFD700' }]}>+{summary.total_status_boost} pts</Text>
              </View>
            </View>
          </View>
        )}

        {/* OWNED */}
        {viewMode === 'owned' && filtered.length === 0 && (
          <View style={s.empty}>
            <Ionicons name="diamond-outline" size={64} color={colors.textSecondary} />
            <Text style={[s.emptyTitle, { color: colors.text }]}>{t('assets.noAssets')}</Text>
            <Text style={[s.emptySub, { color: colors.textSecondary }]}>{t('assets.buyHint')}</Text>
            <TouchableOpacity style={s.goBtn} onPress={() => setViewMode('store')}>
              <Text style={s.goBtnText}>{t('assets.goToStore')}</Text>
            </TouchableOpacity>
          </View>
        )}

        {viewMode === 'owned' && filtered.map(a => {
          const catCfg = CATEGORY_CONFIG[a.category] || { color: '#888', icon: 'cube', label: '' };
          const isProfit = a.profit >= 0;
          return (
            <View key={a.id} style={[s.assetCard, { backgroundColor: colors.card, borderLeftColor: catCfg.color, borderLeftWidth: 4 }]}>
              <View style={s.aHeader}>
                <View style={[s.aIcon, { backgroundColor: catCfg.color }]}><Ionicons name={a.icon as any || catCfg.icon as any} size={22} color="#fff" /></View>
                <View style={s.aInfo}>
                  <Text style={[s.aName, { color: colors.text }]}>{a.name}</Text>
                  <Text style={[s.aSub, { color: colors.textSecondary }]}>{a.subcategory}</Text>
                </View>
                <View style={s.aValues}>
                  <Text style={[s.aValue, { color: colors.text }]}>{formatMoney(a.current_value)}</Text>
                  <Text style={[s.aProfit, { color: isProfit ? '#4CAF50' : '#F44336' }]}>
                    {isProfit ? '+' : ''}{safeFixed(a.profit_pct, 1)}%
                  </Text>
                </View>
              </View>
              <Text style={[s.aDesc, { color: colors.textSecondary }]}>{a.description}</Text>
              <View style={s.aFooter}>
                <Text style={s.aStatus}>{t('assets.statusBoost')}: +{a.status_boost} pts</Text>
                <TouchableOpacity style={[s.sellBtn, { borderColor: '#F44336', backgroundColor: colors.background }]} onPress={() => handleSell(a)}>
                  <Text style={s.sellText}>{t('assets.sell')}</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* OFFERS */}
        {viewMode === 'offers' && offers.length === 0 && (
          <View style={s.empty}>
            <Ionicons name="pricetag-outline" size={64} color={colors.textSecondary} />
            <Text style={[s.emptyTitle, { color: colors.text }]}>{t('assets.noOffers')}</Text>
            <Text style={[s.emptySub, { color: colors.textSecondary }]}>{t('assets.offersHint')}</Text>
          </View>
        )}

        {viewMode === 'offers' && offers.map(offer => {
          const isProfit = offer.offer_amount >= offer.purchase_price;
          const profitPct = offer.purchase_price > 0 ? safeFixed((offer.offer_amount - offer.purchase_price) / offer.purchase_price * 100, 0) : '0';
          const hrs = Math.floor(offer.remaining_minutes / 60);
          const mins = offer.remaining_minutes % 60;
          return (
            <View key={offer.id} style={[s.assetCard, { backgroundColor: colors.card, borderLeftColor: offer.reason_type === 'high' ? '#4CAF50' : offer.reason_type === 'low' ? '#F44336' : '#FF9800', borderLeftWidth: 4 }]}>
              <View style={s.aHeader}>
                <View style={[s.aIcon, { backgroundColor: offer.reason_type === 'high' ? '#4CAF50' : offer.reason_type === 'low' ? '#F44336' : '#FF9800' }]}>
                  <Text style={{ fontSize: 20 }}>{offer.reason_emoji}</Text>
                </View>
                <View style={s.aInfo}>
                  <Text style={[s.aName, { color: colors.text }]}>{offer.asset_name}</Text>
                  <Text style={[s.aSub, { color: colors.textSecondary }]}>{t('assets.offerFrom')}: {offer.buyer_name}</Text>
                </View>
                <View style={s.aValues}>
                  <Text style={[s.aValue, { color: '#FFD700' }]}>{formatMoney(offer.offer_amount)}</Text>
                  <Text style={[s.aProfit, { color: isProfit ? '#4CAF50' : '#F44336' }]}>
                    {isProfit ? '+' : ''}{profitPct}%
                  </Text>
                </View>
              </View>
              <Text style={[s.aDesc, { color: colors.textSecondary }]}>{offer.reason}</Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, marginBottom: 8 }}>
                <Text style={{ color: colors.textSecondary, fontSize: 11 }}>{t('assets.boughtFor')}: {formatMoney(offer.purchase_price)}</Text>
                <Text style={{ color: '#FF9800', fontSize: 11, fontWeight: '600' }}>{t('assets.expiresIn')} {hrs}h {mins}min</Text>
              </View>
              <View style={{ flexDirection: 'row', gap: 10 }}>
                <TouchableOpacity
                  style={{ flex: 1, backgroundColor: '#4CAF50', borderRadius: 10, padding: 12, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6 }}
                  onPress={() => handleOfferRespond(offer, 'accept')}
                  disabled={respondingOffer === offer.id}
                >
                  {respondingOffer === offer.id ? <ActivityIndicator size="small" color="#fff" /> : <Ionicons name="checkmark" size={18} color="#fff" />}
                  <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 14 }}>{t('assets.accept')}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={{ flex: 1, backgroundColor: colors.card, borderRadius: 10, padding: 12, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, borderWidth: 1, borderColor: colors.border }}
                  onPress={() => handleOfferRespond(offer, 'decline')}
                  disabled={respondingOffer === offer.id}
                >
                  <Ionicons name="close" size={18} color="#F44336" />
                  <Text style={{ color: '#F44336', fontWeight: '600', fontSize: 14 }}>{t('assets.decline')}</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* STORE */}
        {viewMode === 'store' && filtered.map(a => {
          const catCfg = CATEGORY_CONFIG[a.category] || { color: '#888', icon: 'cube', label: '' };
          const canAfford = (user?.money || 0) >= a.price;
          const hasLevel = (user?.level || 1) >= a.level_required;
          const appreciation = a.appreciation;
          return (
            <View key={a.id} style={[s.storeCard, { backgroundColor: colors.card }, a.already_owned && { opacity: 0.5 }]}>
              <View style={s.aHeader}>
                <View style={[s.aIcon, { backgroundColor: catCfg.color, width: 52, height: 52, borderRadius: 14 }]}><Ionicons name={a.icon as any || catCfg.icon as any} size={28} color="#fff" /></View>
                <View style={s.aInfo}>
                  <Text style={[s.aName, { color: colors.text }]}>{a.name}</Text>
                  <Text style={[s.aSub, { color: colors.textSecondary }]}>{a.subcategory} • {t('profile.levelLabel')} {a.level_required}</Text>
                </View>
                <Text style={s.storePrice}>{formatMoney(a.price)}</Text>
              </View>
              <Text style={[s.aDesc, { color: colors.textSecondary }]}>{a.description}</Text>
              <View style={s.storeMeta}>
                <Text style={[s.metaChip, { color: appreciation >= 0 ? '#4CAF50' : '#F44336' }]}>
                  {appreciation >= 0 ? '+' : ''}{safeFixed((appreciation || 0) * 100, 0)}%{t('assets.perYear')}
                </Text>
                <Text style={[s.metaChip, { color: colors.textSecondary }]}>+{a.status_boost} {t('assets.statusBoost').toLowerCase()}</Text>
              </View>
              {a.already_owned ? (
                <View style={s.ownedBadge}><Ionicons name="checkmark-circle" size={16} color="#4CAF50" /><Text style={s.ownedText}>{t('assets.alreadyOwned')}</Text></View>
              ) : (
                <TouchableOpacity style={[s.buyBtn, (!canAfford || !hasLevel) && s.disabled]} onPress={() => handleBuy(a)} disabled={buying === a.id}>
                  {buying === a.id ? <ActivityIndicator size="small" color="#fff" /> : (
                    <Text style={s.buyText}>{!hasLevel ? `${t('assets.levelRequired')} ${a.level_required}` : !canAfford ? t('assets.insufficientFunds') : t('assets.buy')}</Text>
                  )}
                </TouchableOpacity>
              )}
            </View>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadText: { fontSize: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1 },
  title: { fontSize: 28, fontWeight: 'bold' },
  content: { padding: 16, paddingBottom: 32 },
  toggle: { flexDirection: 'row', margin: 16, marginBottom: 0, gap: 8 },
  tBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderRadius: 10, gap: 6 },
  tActive: { backgroundColor: '#9C27B0' },
  tText: { fontSize: 13, fontWeight: 'bold' },
  tTextActive: { color: '#fff' },
  filterScroll: { marginHorizontal: 16, marginTop: 12, marginBottom: 4, maxHeight: 40 },
  filterRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  fChip: { flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6, height: 32 },
  fActive: { backgroundColor: '#9C27B0' },
  fText: { fontSize: 12, fontWeight: 'bold' },
  fTextActive: { color: '#fff' },
  summaryCard: { borderRadius: 16, padding: 20, marginBottom: 20 },
  sumLabel: { fontSize: 14 },
  sumValue: { fontSize: 28, fontWeight: 'bold', marginVertical: 8 },
  sumRow: { flexDirection: 'row', justifyContent: 'space-between' },
  sumItem: { flex: 1, alignItems: 'center' },
  sumItemLabel: { fontSize: 11, marginBottom: 4 },
  sumItemVal: { fontSize: 13, fontWeight: 'bold' },
  assetCard: { borderRadius: 12, padding: 16, marginBottom: 12 },
  aHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  aIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  aInfo: { flex: 1 },
  aName: { fontSize: 16, fontWeight: 'bold' },
  aSub: { fontSize: 12, marginTop: 2 },
  aValues: { alignItems: 'flex-end' },
  aValue: { fontSize: 14, fontWeight: 'bold' },
  aProfit: { fontSize: 13, fontWeight: 'bold', marginTop: 2 },
  aDesc: { fontSize: 12, marginBottom: 8 },
  aFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  aStatus: { color: '#FFD700', fontSize: 12, fontWeight: 'bold' },
  sellBtn: { borderRadius: 8, paddingHorizontal: 16, paddingVertical: 8, borderWidth: 1 },
  sellText: { color: '#F44336', fontSize: 13, fontWeight: 'bold' },
  storeCard: { borderRadius: 12, padding: 16, marginBottom: 12 },
  storePrice: { color: '#FFD700', fontSize: 14, fontWeight: 'bold' },
  storeMeta: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  metaChip: { fontSize: 12 },
  buyBtn: { backgroundColor: '#9C27B0', borderRadius: 10, padding: 12, alignItems: 'center' },
  buyText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  ownedBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, padding: 10 },
  ownedText: { color: '#4CAF50', fontWeight: 'bold' },
  disabled: { opacity: 0.5 },
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyTitle: { fontSize: 22, fontWeight: 'bold', marginTop: 16 },
  emptySub: { fontSize: 14, textAlign: 'center', marginTop: 8, maxWidth: 280 },
  goBtn: { backgroundColor: '#9C27B0', borderRadius: 12, paddingHorizontal: 24, paddingVertical: 12, marginTop: 20 },
  goBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
});
