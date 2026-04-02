import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl,
  Alert, ActivityIndicator, Modal, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const CATEGORY_CFG: Record<string, { label: string; icon: string; color: string }> = {
  dinheiro: { label: 'Dinheiro', icon: 'cash', color: '#4CAF50' },
  xp: { label: 'XP', icon: 'star', color: '#FF9800' },
  ganhos: { label: 'Boost Ganhos', icon: 'flash', color: '#E91E63' },
};

export default function Store() {
  const { token, user, refreshUser } = useAuth();
  const { t, formatMoney } = useLanguage();
  const [items, setItems] = useState<any[]>([]);
  const [purchases, setPurchases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterCat, setFilterCat] = useState('all');
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [showPayment, setShowPayment] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [paymentMethod, setPaymentMethod] = useState<'credit_card' | 'pix'>('credit_card');
  const [showHistory, setShowHistory] = useState(false);
  const [dailyStatus, setDailyStatus] = useState<any>(null);
  const [claimingDaily, setClaimingDaily] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const h = { Authorization: `Bearer ${token}` };
      const [itemsRes, purchasesRes, dailyRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/store/items`, { headers: h }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/store/purchases`, { headers: h }).catch(() => ({ data: [] })),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/store/daily-reward-status`, { headers: h }).catch(() => ({ data: null })),
      ]);
      setItems(itemsRes.data);
      setPurchases(purchasesRes.data);
      if (dailyRes.data) setDailyStatus(dailyRes.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = async () => { setRefreshing(true); await loadData(); await refreshUser(); setRefreshing(false); };

  const showAlert = (title: string, msg: string) => {
    if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
    else Alert.alert(title, msg);
  };

  const openPayment = (item: any) => {
    setSelectedItem(item);
    setPaymentMethod('credit_card');
    setShowPayment(true);
  };

  const handlePurchase = async () => {
    if (!selectedItem) return;
    setPurchasing(selectedItem.id);
    setShowPayment(false);
    try {
      const r = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/store/purchase`,
        { item_id: selectedItem.id, payment_method: paymentMethod },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      showAlert('Compra Realizada!', r.data.message);
      await loadData();
      await refreshUser();
    } catch (e: any) {
      showAlert('Erro', e.response?.data?.detail || 'Erro ao processar compra');
    } finally {
      setPurchasing(null);
      setSelectedItem(null);
    }
  };

  const handleDailyReward = async () => {
    setClaimingDaily(true);
    try {
      const r = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/store/daily-reward`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      showAlert('Recompensa Diária!', r.data.message);
      await loadData();
      await refreshUser();
    } catch (e: any) {
      showAlert('Indisponível', e.response?.data?.detail || 'Erro ao resgatar');
    } finally { setClaimingDaily(false); }
  };

  const filtered = filterCat === 'all' ? items : items.filter(i => i.category === filterCat);

  const formatReward = (item: any) => {
    const r = item.game_reward;
    if (r.money) return `+R$ ${r.money.toLocaleString('pt-BR')}`;
    if (r.xp) return `+${r.xp.toLocaleString('pt-BR')} XP`;
    if (r.earnings_multiplier) return `${r.earnings_multiplier}x por ${r.duration_hours}h`;
    return '';
  };

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}>
        <ActivityIndicator size="large" color="#E91E63" />
        <Text style={s.loadText}>{t('general.loading')}</Text>
      </View>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <View>
          <Text style={s.title}>{t('store.title')}</Text>
          <Text style={s.subtitle}>{t('store.title')}</Text>
        </View>
        <TouchableOpacity style={s.historyBtn} onPress={() => setShowHistory(true)}>
          <Ionicons name="receipt" size={22} color="#888" />
        </TouchableOpacity>
      </View>

      {/* Balance */}
      <View style={s.balanceBar}>
        <View style={s.balanceItem}>
          <Ionicons name="wallet" size={16} color="#4CAF50" />
          <Text style={s.balanceText}>R$ {(user?.money || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</Text>
        </View>
        <View style={s.balanceItem}>
          <Ionicons name="star" size={16} color="#FF9800" />
          <Text style={s.balanceText}>Nv {user?.level || 1}</Text>
        </View>
      </View>

      {/* Category Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.filterScroll}>
        <View style={s.filterRow}>
          <TouchableOpacity style={[s.fChip, filterCat === 'all' && s.fActive]} onPress={() => setFilterCat('all')}>
            <Ionicons name="grid" size={14} color={filterCat === 'all' ? '#fff' : '#888'} />
            <Text style={[s.fText, filterCat === 'all' && s.fTextActive]}>{t('store.all')}</Text>
          </TouchableOpacity>
          {Object.entries(CATEGORY_CFG).map(([key, cfg]) => (
            <TouchableOpacity key={key} style={[s.fChip, filterCat === key && { backgroundColor: cfg.color }]} onPress={() => setFilterCat(key)}>
              <Ionicons name={cfg.icon as any} size={14} color={filterCat === key ? '#fff' : '#888'} />
              <Text style={[s.fText, filterCat === key && s.fTextActive]}>{cfg.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Items */}
      <ScrollView contentContainerStyle={s.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#E91E63" />}>
        {/* Daily Free Money */}
        {dailyStatus?.available && (
          <TouchableOpacity
            style={[s.dailyCard, claimingDaily && { opacity: 0.5 }]}
            onPress={handleDailyReward}
            disabled={claimingDaily}
            activeOpacity={0.7}
          >
            <View style={s.dailyLeft}>
              <View style={s.dailyIconBg}>
                <Ionicons name="gift" size={28} color="#FFD700" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.dailyTitle}>{t('store.dailyReward')}</Text>
                <Text style={s.dailyDesc}>Assista uma propaganda e ganhe R$ {dailyStatus.reward_amount?.toLocaleString('pt-BR')}</Text>
              </View>
            </View>
            {claimingDaily ? (
              <ActivityIndicator size="small" color="#FFD700" />
            ) : (
              <View style={s.dailyBtn}>
                <Ionicons name="play-circle" size={20} color="#000" />
                <Text style={s.dailyBtnText}>{t('store.dailyClaim')}</Text>
              </View>
            )}
          </TouchableOpacity>
        )}
        {dailyStatus && !dailyStatus.available && (
          <View style={[s.dailyCard, { borderColor: '#333', opacity: 0.6 }]}>
            <View style={s.dailyLeft}>
              <View style={[s.dailyIconBg, { backgroundColor: '#333' }]}>
                <Ionicons name="checkmark-circle" size={28} color="#4CAF50" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[s.dailyTitle, { color: '#666' }]}>{t('store.dailyClaimed')}</Text>
                <Text style={s.dailyDesc}>Volte amanhã para ganhar mais</Text>
              </View>
            </View>
          </View>
        )}

        {/* Mock Payment Notice */}
        <View style={s.mockNotice}>
          <Ionicons name="information-circle" size={18} color="#FF9800" />
          <Text style={s.mockText}>Modo demonstração - pagamentos simulados. Integração com cartão e PIX em breve!</Text>
        </View>

        {filtered.map(item => {
          const catCfg = CATEGORY_CFG[item.category] || { color: '#888', icon: 'cube', label: '' };
          const isPurchasing = purchasing === item.id;
          return (
            <View key={item.id} style={s.itemCard}>
              {/* Badges */}
              {item.popular && (
                <View style={s.popularBadge}>
                  <Ionicons name="flame" size={12} color="#fff" />
                  <Text style={s.badgeText}>POPULAR</Text>
                </View>
              )}
              {item.best_value && (
                <View style={[s.popularBadge, { backgroundColor: '#FFD700', right: item.popular ? 90 : 0 }]}>
                  <Ionicons name="star" size={12} color="#000" />
                  <Text style={[s.badgeText, { color: '#000' }]}>MELHOR VALOR</Text>
                </View>
              )}

              <View style={s.itemHeader}>
                <View style={[s.itemIcon, { backgroundColor: catCfg.color }]}>
                  <Ionicons name={(item.icon || catCfg.icon) as any} size={24} color="#fff" />
                </View>
                <View style={s.itemInfo}>
                  <Text style={s.itemName}>{item.name}</Text>
                  <Text style={s.itemDesc}>{item.description}</Text>
                </View>
              </View>

              <View style={s.rewardRow}>
                <View style={[s.rewardBadge, { backgroundColor: `${catCfg.color}20` }]}>
                  <Text style={[s.rewardText, { color: catCfg.color }]}>{formatReward(item)}</Text>
                </View>
              </View>

              <TouchableOpacity
                style={[s.buyBtn, { backgroundColor: catCfg.color }, isPurchasing && s.disabled]}
                onPress={() => openPayment(item)}
                disabled={isPurchasing}
              >
                {isPurchasing ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <>
                    <Text style={s.buyPrice}>R$ {item.price_brl.toFixed(2).replace('.', ',')}</Text>
                    <Ionicons name="cart" size={18} color="#fff" />
                  </>
                )}
              </TouchableOpacity>
            </View>
          );
        })}
      </ScrollView>

      {/* Payment Modal */}
      <Modal visible={showPayment} animationType="slide" transparent onRequestClose={() => setShowPayment(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>{t('store.confirm')}</Text>
              <TouchableOpacity onPress={() => setShowPayment(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            {selectedItem && (
              <>
                {/* Item Summary */}
                <View style={s.summaryCard}>
                  <View style={[s.sumIcon, { backgroundColor: CATEGORY_CFG[selectedItem.category]?.color || '#888' }]}>
                    <Ionicons name={(selectedItem.icon || 'cube') as any} size={28} color="#fff" />
                  </View>
                  <Text style={s.sumName}>{selectedItem.name}</Text>
                  <Text style={s.sumReward}>{formatReward(selectedItem)}</Text>
                  <Text style={s.sumPrice}>R$ {selectedItem.price_brl.toFixed(2).replace('.', ',')}</Text>
                </View>

                {/* Payment Method */}
                <Text style={s.label}>{t('store.paymentMethod')}</Text>
                <View style={s.payMethods}>
                  <TouchableOpacity
                    style={[s.payOption, paymentMethod === 'credit_card' && s.payActive]}
                    onPress={() => setPaymentMethod('credit_card')}
                  >
                    <Ionicons name="card" size={24} color={paymentMethod === 'credit_card' ? '#fff' : '#888'} />
                    <Text style={[s.payLabel, paymentMethod === 'credit_card' && s.payLabelActive]}>{t('store.creditCard')}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[s.payOption, paymentMethod === 'pix' && s.payActive]}
                    onPress={() => setPaymentMethod('pix')}
                  >
                    <Ionicons name="qr-code" size={24} color={paymentMethod === 'pix' ? '#fff' : '#888'} />
                    <Text style={[s.payLabel, paymentMethod === 'pix' && s.payLabelActive]}>{t('store.pix')}</Text>
                  </TouchableOpacity>
                </View>

                {/* Mock Notice */}
                <View style={s.mockNoticeModal}>
                  <Ionicons name="shield-checkmark" size={16} color="#4CAF50" />
                  <Text style={s.mockTextModal}>Modo demo - nenhum valor real será cobrado</Text>
                </View>

                <TouchableOpacity style={s.confirmBtn} onPress={handlePurchase}>
                  <Ionicons name="lock-closed" size={18} color="#fff" />
                  <Text style={s.confirmText}>Comprar por R$ {selectedItem.price_brl.toFixed(2).replace('.', ',')}</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Modal>

      {/* Purchase History Modal */}
      <Modal visible={showHistory} animationType="slide" transparent onRequestClose={() => setShowHistory(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>{t('store.purchaseHistory')}</Text>
              <TouchableOpacity onPress={() => setShowHistory(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>
            <ScrollView style={{ maxHeight: 400 }}>
              {purchases.length === 0 ? (
                <View style={s.emptyHistory}>
                  <Ionicons name="receipt-outline" size={48} color="#555" />
                  <Text style={s.emptyHistText}>{t('store.noPurchases')}</Text>
                </View>
              ) : purchases.map((p: any, i: number) => (
                <View key={p.id || i} style={s.histItem}>
                  <View style={s.histInfo}>
                    <Text style={s.histName}>{p.item_name}</Text>
                    <Text style={s.histDate}>
                      {p.created_at ? new Date(p.created_at).toLocaleDateString('pt-BR') : ''}
                      {' • '}{p.payment_method === 'pix' ? 'PIX' : 'Cartão'}
                    </Text>
                  </View>
                  <Text style={s.histPrice}>R$ {p.price_brl?.toFixed(2).replace('.', ',')}</Text>
                </View>
              ))}
            </ScrollView>
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
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 13, color: '#888', marginTop: 2 },
  historyBtn: { width: 44, height: 44, borderRadius: 12, backgroundColor: '#2a2a2a', justifyContent: 'center', alignItems: 'center' },
  // Balance
  balanceBar: { flexDirection: 'row', justifyContent: 'space-around', padding: 12, backgroundColor: '#2a2a2a', marginHorizontal: 16, marginTop: 12, borderRadius: 12 },
  balanceItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  balanceText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  // Filter
  filterScroll: { marginHorizontal: 16, marginTop: 12, marginBottom: 4 },
  filterRow: { flexDirection: 'row', gap: 8 },
  fChip: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#2a2a2a', borderRadius: 16, paddingHorizontal: 14, paddingVertical: 8 },
  fActive: { backgroundColor: '#E91E63' },
  fText: { color: '#888', fontSize: 13, fontWeight: 'bold' },
  fTextActive: { color: '#fff' },
  content: { padding: 16, paddingBottom: 32 },
  // Daily Free Money
  dailyCard: { backgroundColor: '#1a2a1a', borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: '#FFD700' },
  dailyLeft: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  dailyIconBg: { width: 50, height: 50, borderRadius: 25, backgroundColor: '#FFD70020', justifyContent: 'center', alignItems: 'center' },
  dailyTitle: { color: '#FFD700', fontSize: 16, fontWeight: 'bold' },
  dailyDesc: { color: '#888', fontSize: 12, marginTop: 2 },
  dailyBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: '#FFD700', borderRadius: 12, paddingVertical: 12 },
  dailyBtnText: { color: '#000', fontSize: 14, fontWeight: 'bold' },
  // Mock Notice
  mockNotice: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#2a2a1a', borderRadius: 10, padding: 12, marginBottom: 16, borderWidth: 1, borderColor: '#FF9800' },
  mockText: { flex: 1, color: '#FF9800', fontSize: 12 },
  // Item Card
  itemCard: { backgroundColor: '#2a2a2a', borderRadius: 16, padding: 16, marginBottom: 12, position: 'relative' as any },
  popularBadge: { position: 'absolute' as any, top: -6, right: 0, backgroundColor: '#E91E63', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3, flexDirection: 'row', alignItems: 'center', gap: 4, zIndex: 1 },
  badgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  itemHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  itemIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  itemInfo: { flex: 1 },
  itemName: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  itemDesc: { color: '#888', fontSize: 13, marginTop: 4 },
  rewardRow: { marginBottom: 12 },
  rewardBadge: { alignSelf: 'flex-start', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 6 },
  rewardText: { fontSize: 16, fontWeight: 'bold' },
  buyBtn: { borderRadius: 12, padding: 14, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  buyPrice: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  disabled: { opacity: 0.5 },
  // Payment Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'flex-end' },
  modal: { backgroundColor: '#1a1a1a', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, maxHeight: '85%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  modalTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  summaryCard: { alignItems: 'center', backgroundColor: '#2a2a2a', borderRadius: 16, padding: 24, marginBottom: 20 },
  sumIcon: { width: 56, height: 56, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  sumName: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  sumReward: { color: '#4CAF50', fontSize: 16, fontWeight: 'bold', marginBottom: 8 },
  sumPrice: { color: '#FFD700', fontSize: 28, fontWeight: 'bold' },
  label: { color: '#888', fontSize: 14, marginBottom: 12 },
  payMethods: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  payOption: { flex: 1, alignItems: 'center', padding: 16, borderRadius: 12, backgroundColor: '#2a2a2a', borderWidth: 2, borderColor: '#3a3a3a', gap: 8 },
  payActive: { borderColor: '#E91E63', backgroundColor: '#2a1a2a' },
  payLabel: { color: '#888', fontSize: 13, fontWeight: 'bold' },
  payLabelActive: { color: '#fff' },
  mockNoticeModal: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16, padding: 10, backgroundColor: '#1a2a1a', borderRadius: 8 },
  mockTextModal: { color: '#4CAF50', fontSize: 12 },
  confirmBtn: { backgroundColor: '#E91E63', borderRadius: 14, padding: 18, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  confirmText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  // History
  emptyHistory: { alignItems: 'center', paddingVertical: 32 },
  emptyHistText: { color: '#666', fontSize: 16, marginTop: 12 },
  histItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
  histInfo: { flex: 1 },
  histName: { color: '#fff', fontSize: 15, fontWeight: '600' },
  histDate: { color: '#666', fontSize: 12, marginTop: 4 },
  histPrice: { color: '#FFD700', fontSize: 15, fontWeight: 'bold' },
});
