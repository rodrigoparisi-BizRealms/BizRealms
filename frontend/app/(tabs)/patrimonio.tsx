import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl,
  Alert, ActivityIndicator, Platform, Modal, Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const CATEGORY_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  veiculo: { label: 'Veículos', icon: 'car-sport', color: '#2196F3' },
  imovel: { label: 'Imóveis', icon: 'home', color: '#FF9800' },
  luxo: { label: 'Luxo', icon: 'diamond', color: '#9C27B0' },
};

export default function Patrimonio() {
  const { token, user, refreshUser } = useAuth();
  const [store, setStore] = useState<any[]>([]);
  const [owned, setOwned] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'owned' | 'store' | 'offers'>('owned');
  const [filterCat, setFilterCat] = useState('all');
  const [buying, setBuying] = useState<string | null>(null);
  const [showGallery, setShowGallery] = useState(false);
  const [galleryImages, setGalleryImages] = useState<string[]>([]);
  const [galleryName, setGalleryName] = useState('');
  const [galleryIdx, setGalleryIdx] = useState(0);
  const [offers, setOffers] = useState<any[]>([]);
  const [respondingOffer, setRespondingOffer] = useState<string | null>(null);

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

  const showAlert = (t: string, m: string) => {
    if (Platform.OS === 'web') window.alert(`${t}\n\n${m}`);
    else Alert.alert(t, m);
  };

  const confirmAction = (t: string, m: string, onOk: () => void) => {
    if (Platform.OS === 'web') { if (window.confirm(`${t}\n\n${m}`)) onOk(); }
    else Alert.alert(t, m, [{ text: 'Cancelar', style: 'cancel' }, { text: 'Confirmar', onPress: onOk }]);
  };

  const handleBuy = (asset: any) => {
    confirmAction('Comprar', `Deseja comprar ${asset.name} por R$ ${asset.price.toLocaleString('pt-BR')}?\n\n${asset.description}\n\nValorização: ${asset.appreciation > 0 ? '+' : ''}${(asset.appreciation * 100).toFixed(0)}%/mês`, async () => {
      setBuying(asset.id);
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/buy`, { asset_id: asset.id }, { headers: { Authorization: `Bearer ${token}` } });
        showAlert('Compra Realizada!', `${r.data.message}\nStatus: +${r.data.status_boost} pontos`);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert('Erro', e.response?.data?.detail || 'Erro'); }
      finally { setBuying(null); }
    });
  };

  const handleSell = (asset: any) => {
    const profit = asset.profit >= 0 ? `Lucro: R$ ${asset.profit.toFixed(2)}` : `Prejuízo: R$ ${Math.abs(asset.profit).toFixed(2)}`;
    confirmAction('Vender', `Vender ${asset.name}?\n\nValor atual: R$ ${asset.current_value.toLocaleString('pt-BR')}\n${profit}`, async () => {
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/sell`, { asset_id: asset.id }, { headers: { Authorization: `Bearer ${token}` } });
        showAlert('Venda Realizada!', r.data.message);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert('Erro', e.response?.data?.detail || 'Erro'); }
    });
  };

  const handleOfferRespond = (offer: any, action: 'accept' | 'decline') => {
    const msg = action === 'accept'
      ? `Aceitar oferta de ${offer.buyer_name} de R$ ${offer.offer_amount.toLocaleString('pt-BR')} por "${offer.asset_name}"?`
      : `Recusar oferta de ${offer.buyer_name}?`;
    confirmAction(action === 'accept' ? 'Aceitar Oferta' : 'Recusar Oferta', msg, async () => {
      setRespondingOffer(offer.id);
      try {
        const r = await axios.post(
          `${EXPO_PUBLIC_BACKEND_URL}/api/assets/offers/respond`,
          { offer_id: offer.id, action },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        showAlert(action === 'accept' ? 'Vendido!' : 'Recusado', r.data.message);
        await loadData(); await refreshUser();
      } catch (e: any) { showAlert('Erro', e.response?.data?.detail || 'Erro'); }
      finally { setRespondingOffer(null); }
    });
  };

  const openGallery = async (asset: any) => {
    setGalleryName(asset.name);
    setGalleryIdx(0);
    try {
      // Generate a key from the asset name for image lookup
      const nameKey = asset.name.toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
      const r = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/assets/images/${nameKey}`);
      setGalleryImages(r.data.images || []);
    } catch {
      setGalleryImages([]);
    }
    setShowGallery(true);
  };

  const filtered = filterCat === 'all' ? (viewMode === 'store' ? store : owned) : (viewMode === 'store' ? store : owned).filter(a => a.category === filterCat);

  if (loading) return (<SafeAreaView style={s.container}><View style={s.center}><ActivityIndicator size="large" color="#9C27B0" /><Text style={s.loadText}>Carregando patrimônio...</Text></View></SafeAreaView>);

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}><Text style={s.title}>Patrimônio</Text><Ionicons name="diamond" size={28} color="#9C27B0" /></View>

      {/* Mode Toggle */}
      <View style={s.toggle}>
        <TouchableOpacity style={[s.tBtn, viewMode === 'owned' && s.tActive]} onPress={() => setViewMode('owned')}>
          <Ionicons name="wallet" size={16} color={viewMode === 'owned' ? '#fff' : '#888'} />
          <Text style={[s.tText, viewMode === 'owned' && s.tTextActive]}>Meus Bens ({owned.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[s.tBtn, viewMode === 'offers' && { backgroundColor: '#FF9800' }]} onPress={() => setViewMode('offers')}>
          <Ionicons name="pricetag" size={16} color={viewMode === 'offers' ? '#fff' : '#888'} />
          <Text style={[s.tText, viewMode === 'offers' && s.tTextActive]}>Ofertas {offers.length > 0 ? `(${offers.length})` : ''}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[s.tBtn, viewMode === 'store' && s.tActive]} onPress={() => setViewMode('store')}>
          <Ionicons name="cart" size={16} color={viewMode === 'store' ? '#fff' : '#888'} />
          <Text style={[s.tText, viewMode === 'store' && s.tTextActive]}>Loja</Text>
        </TouchableOpacity>
      </View>

      {/* Category Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.filterScroll}>
        <View style={s.filterRow}>
          <TouchableOpacity style={[s.fChip, filterCat === 'all' && s.fActive]} onPress={() => setFilterCat('all')}>
            <Text style={[s.fText, filterCat === 'all' && s.fTextActive]}>Todos</Text>
          </TouchableOpacity>
          {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => (
            <TouchableOpacity key={key} style={[s.fChip, filterCat === key && { backgroundColor: cfg.color }]} onPress={() => setFilterCat(key)}>
              <Ionicons name={cfg.icon as any} size={14} color={filterCat === key ? '#fff' : '#888'} />
              <Text style={[s.fText, filterCat === key && s.fTextActive]}>{cfg.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <ScrollView contentContainerStyle={s.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#9C27B0" />}>
        {/* Portfolio Summary */}
        {viewMode === 'owned' && summary && summary.count > 0 && (
          <View style={s.summaryCard}>
            <Text style={s.sumLabel}>Valor Total do Patrimônio</Text>
            <Text style={s.sumValue}>R$ {summary.total_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</Text>
            <View style={s.sumRow}>
              <View style={s.sumItem}>
                <Text style={s.sumItemLabel}>Investido</Text>
                <Text style={s.sumItemVal}>R$ {summary.total_invested.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</Text>
              </View>
              <View style={s.sumItem}>
                <Text style={s.sumItemLabel}>Lucro/Prejuízo</Text>
                <Text style={[s.sumItemVal, { color: summary.total_profit >= 0 ? '#4CAF50' : '#F44336' }]}>
                  {summary.total_profit >= 0 ? '+' : ''}R$ {summary.total_profit.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </Text>
              </View>
              <View style={s.sumItem}>
                <Text style={s.sumItemLabel}>Status</Text>
                <Text style={[s.sumItemVal, { color: '#FFD700' }]}>+{summary.total_status_boost} pts</Text>
              </View>
            </View>
          </View>
        )}

        {/* OWNED */}
        {viewMode === 'owned' && filtered.length === 0 && (
          <View style={s.empty}><Ionicons name="diamond-outline" size={64} color="#555" /><Text style={s.emptyTitle}>Nenhum bem</Text><Text style={s.emptySub}>Compre veículos, imóveis e itens de luxo na loja</Text>
            <TouchableOpacity style={s.goBtn} onPress={() => setViewMode('store')}><Text style={s.goBtnText}>Ir para Loja</Text></TouchableOpacity></View>
        )}

        {viewMode === 'owned' && filtered.map(a => {
          const catCfg = CATEGORY_CONFIG[a.category] || { color: '#888', icon: 'cube', label: '' };
          const isProfit = a.profit >= 0;
          return (
            <View key={a.id} style={[s.assetCard, { borderLeftColor: catCfg.color, borderLeftWidth: 4 }]}>
              <View style={s.aHeader}>
                <View style={[s.aIcon, { backgroundColor: catCfg.color }]}><Ionicons name={a.icon as any || catCfg.icon as any} size={22} color="#fff" /></View>
                <View style={s.aInfo}>
                  <Text style={s.aName}>{a.name}</Text>
                  <Text style={s.aSub}>{a.subcategory}</Text>
                </View>
                <View style={s.aValues}>
                  <Text style={s.aValue}>R$ {a.current_value.toLocaleString('pt-BR')}</Text>
                  <Text style={[s.aProfit, { color: isProfit ? '#4CAF50' : '#F44336' }]}>
                    {isProfit ? '+' : ''}{a.profit_pct.toFixed(1)}%
                  </Text>
                </View>
              </View>
              <Text style={s.aDesc}>{a.description}</Text>
              <View style={s.aFooter}>
                <Text style={s.aStatus}>Status: +{a.status_boost} pts</Text>
                <TouchableOpacity style={s.sellBtn} onPress={() => handleSell(a)}>
                  <Text style={s.sellText}>Vender</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* OFFERS */}
        {viewMode === 'offers' && offers.length === 0 && (
          <View style={s.empty}>
            <Ionicons name="pricetag-outline" size={64} color="#555" />
            <Text style={s.emptyTitle}>Nenhuma oferta</Text>
            <Text style={s.emptySub}>Ofertas de compra para seus bens aparecerão aqui. Compre mais ativos para receber mais ofertas!</Text>
          </View>
        )}

        {viewMode === 'offers' && offers.map(offer => {
          const isProfit = offer.offer_amount >= offer.purchase_price;
          const profitPct = offer.purchase_price > 0 ? ((offer.offer_amount - offer.purchase_price) / offer.purchase_price * 100).toFixed(0) : '0';
          const hrs = Math.floor(offer.remaining_minutes / 60);
          const mins = offer.remaining_minutes % 60;
          return (
            <View key={offer.id} style={[s.assetCard, { borderLeftColor: offer.reason_type === 'high' ? '#4CAF50' : offer.reason_type === 'low' ? '#F44336' : '#FF9800', borderLeftWidth: 4 }]}>
              <View style={s.aHeader}>
                <View style={[s.aIcon, { backgroundColor: offer.reason_type === 'high' ? '#4CAF50' : offer.reason_type === 'low' ? '#F44336' : '#FF9800' }]}>
                  <Text style={{ fontSize: 20 }}>{offer.reason_emoji}</Text>
                </View>
                <View style={s.aInfo}>
                  <Text style={s.aName}>{offer.asset_name}</Text>
                  <Text style={s.aSub}>De: {offer.buyer_name}</Text>
                </View>
                <View style={s.aValues}>
                  <Text style={[s.aValue, { color: '#FFD700' }]}>R$ {offer.offer_amount.toLocaleString('pt-BR')}</Text>
                  <Text style={[s.aProfit, { color: isProfit ? '#4CAF50' : '#F44336' }]}>
                    {isProfit ? '+' : ''}{profitPct}%
                  </Text>
                </View>
              </View>
              <Text style={s.aDesc}>{offer.reason}</Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, marginBottom: 8 }}>
                <Text style={{ color: '#888', fontSize: 11 }}>Comprado por: R$ {offer.purchase_price.toLocaleString('pt-BR')}</Text>
                <Text style={{ color: '#FF9800', fontSize: 11, fontWeight: '600' }}>Expira em {hrs}h {mins}min</Text>
              </View>
              <View style={{ flexDirection: 'row', gap: 10 }}>
                <TouchableOpacity
                  style={{ flex: 1, backgroundColor: '#4CAF50', borderRadius: 10, padding: 12, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6 }}
                  onPress={() => handleOfferRespond(offer, 'accept')}
                  disabled={respondingOffer === offer.id}
                >
                  {respondingOffer === offer.id ? <ActivityIndicator size="small" color="#fff" /> : <Ionicons name="checkmark" size={18} color="#fff" />}
                  <Text style={{ color: '#fff', fontWeight: 'bold', fontSize: 14 }}>Aceitar</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={{ flex: 1, backgroundColor: '#2a2a2a', borderRadius: 10, padding: 12, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, borderWidth: 1, borderColor: '#3a3a3a' }}
                  onPress={() => handleOfferRespond(offer, 'decline')}
                  disabled={respondingOffer === offer.id}
                >
                  <Ionicons name="close" size={18} color="#F44336" />
                  <Text style={{ color: '#F44336', fontWeight: '600', fontSize: 14 }}>Recusar</Text>
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
            <View key={a.id} style={[s.storeCard, a.already_owned && { opacity: 0.5 }]}>
              <View style={s.aHeader}>
                <View style={[s.aIcon, { backgroundColor: catCfg.color }]}><Ionicons name={a.icon as any || catCfg.icon as any} size={22} color="#fff" /></View>
                <View style={s.aInfo}>
                  <Text style={s.aName}>{a.name}</Text>
                  <Text style={s.aSub}>{a.subcategory} • Nível {a.level_required}</Text>
                </View>
                <Text style={s.storePrice}>R$ {a.price.toLocaleString('pt-BR')}</Text>
              </View>
              <Text style={s.aDesc}>{a.description}</Text>
              <TouchableOpacity style={s.photoBtn} onPress={() => openGallery(a)}>
                <Ionicons name="images" size={16} color="#9C27B0" />
                <Text style={s.photoBtnText}>Ver Fotos</Text>
              </TouchableOpacity>
              <View style={s.storeMeta}>
                <Text style={[s.metaChip, { color: appreciation >= 0 ? '#4CAF50' : '#F44336' }]}>
                  {appreciation >= 0 ? '📈' : '📉'} {appreciation > 0 ? '+' : ''}{(appreciation * 100).toFixed(0)}%/mês
                </Text>
                <Text style={s.metaChip}>⭐ +{a.status_boost} status</Text>
              </View>
              {a.already_owned ? (
                <View style={s.ownedBadge}><Ionicons name="checkmark-circle" size={16} color="#4CAF50" /><Text style={s.ownedText}>Já possui</Text></View>
              ) : (
                <TouchableOpacity style={[s.buyBtn, (!canAfford || !hasLevel) && s.disabled]} onPress={() => handleBuy(a)} disabled={buying === a.id}>
                  {buying === a.id ? <ActivityIndicator size="small" color="#fff" /> : (
                    <Text style={s.buyText}>{!hasLevel ? `Requer Nível ${a.level_required}` : !canAfford ? 'Saldo Insuficiente' : 'Comprar'}</Text>
                  )}
                </TouchableOpacity>
              )}
            </View>
          );
        })}
      </ScrollView>

      {/* Image Gallery Modal */}
      <Modal visible={showGallery} animationType="fade" transparent onRequestClose={() => setShowGallery(false)}>
        <View style={s.galleryOverlay}>
          <View style={s.galleryHeader}>
            <Text style={s.galleryTitle}>{galleryName}</Text>
            <TouchableOpacity onPress={() => setShowGallery(false)}>
              <Ionicons name="close" size={28} color="#fff" />
            </TouchableOpacity>
          </View>
          {galleryImages.length > 0 ? (
            <>
              <Image source={{ uri: galleryImages[galleryIdx] }} style={s.galleryImage} resizeMode="cover" />
              <View style={s.galleryNav}>
                <TouchableOpacity style={s.galleryNavBtn} onPress={() => setGalleryIdx(i => Math.max(0, i - 1))} disabled={galleryIdx === 0}>
                  <Ionicons name="chevron-back" size={28} color={galleryIdx === 0 ? '#444' : '#fff'} />
                </TouchableOpacity>
                <Text style={s.galleryCount}>{galleryIdx + 1} / {galleryImages.length}</Text>
                <TouchableOpacity style={s.galleryNavBtn} onPress={() => setGalleryIdx(i => Math.min(galleryImages.length - 1, i + 1))} disabled={galleryIdx >= galleryImages.length - 1}>
                  <Ionicons name="chevron-forward" size={28} color={galleryIdx >= galleryImages.length - 1 ? '#444' : '#fff'} />
                </TouchableOpacity>
              </View>
              <ScrollView horizontal style={s.thumbRow}>
                {galleryImages.map((img, i) => (
                  <TouchableOpacity key={i} onPress={() => setGalleryIdx(i)}>
                    <Image source={{ uri: img }} style={[s.thumb, i === galleryIdx && s.thumbActive]} />
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </>
          ) : (
            <View style={s.center}><Text style={s.loadText}>Sem fotos disponíveis</Text></View>
          )}
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
  content: { padding: 16, paddingBottom: 32 },
  toggle: { flexDirection: 'row', margin: 16, marginBottom: 0, gap: 8 },
  tBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderRadius: 10, backgroundColor: '#2a2a2a', gap: 6 },
  tActive: { backgroundColor: '#9C27B0' },
  tText: { color: '#888', fontSize: 13, fontWeight: 'bold' },
  tTextActive: { color: '#fff' },
  filterScroll: { marginHorizontal: 16, marginTop: 12, marginBottom: 4, maxHeight: 40 },
  filterRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  fChip: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#2a2a2a', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6, height: 32 },
  fActive: { backgroundColor: '#9C27B0' },
  fText: { color: '#888', fontSize: 12, fontWeight: 'bold' },
  fTextActive: { color: '#fff' },
  // Summary
  summaryCard: { backgroundColor: '#2a2a2a', borderRadius: 16, padding: 20, marginBottom: 20 },
  sumLabel: { color: '#888', fontSize: 14 },
  sumValue: { color: '#fff', fontSize: 28, fontWeight: 'bold', marginVertical: 8 },
  sumRow: { flexDirection: 'row', justifyContent: 'space-between' },
  sumItem: { flex: 1, alignItems: 'center' },
  sumItemLabel: { color: '#666', fontSize: 11, marginBottom: 4 },
  sumItemVal: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  // Asset Card
  assetCard: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, marginBottom: 12 },
  aHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  aIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  aInfo: { flex: 1 },
  aName: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  aSub: { color: '#888', fontSize: 12, marginTop: 2 },
  aValues: { alignItems: 'flex-end' },
  aValue: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  aProfit: { fontSize: 13, fontWeight: 'bold', marginTop: 2 },
  aDesc: { color: '#888', fontSize: 12, marginBottom: 8 },
  aFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  aStatus: { color: '#FFD700', fontSize: 12, fontWeight: 'bold' },
  sellBtn: { backgroundColor: '#2a2a2a', borderRadius: 8, paddingHorizontal: 16, paddingVertical: 8, borderWidth: 1, borderColor: '#F44336' },
  sellText: { color: '#F44336', fontSize: 13, fontWeight: 'bold' },
  // Store Card
  storeCard: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, marginBottom: 12 },
  storePrice: { color: '#FFD700', fontSize: 14, fontWeight: 'bold' },
  storeMeta: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  metaChip: { fontSize: 12, color: '#aaa' },
  buyBtn: { backgroundColor: '#9C27B0', borderRadius: 10, padding: 12, alignItems: 'center' },
  buyText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  ownedBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, padding: 10 },
  ownedText: { color: '#4CAF50', fontWeight: 'bold' },
  disabled: { opacity: 0.5 },
  // Empty
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyTitle: { color: '#fff', fontSize: 22, fontWeight: 'bold', marginTop: 16 },
  emptySub: { color: '#666', fontSize: 14, textAlign: 'center', marginTop: 8, maxWidth: 280 },
  goBtn: { backgroundColor: '#9C27B0', borderRadius: 12, paddingHorizontal: 24, paddingVertical: 12, marginTop: 20 },
  goBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  photoBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8, paddingVertical: 6 },
  photoBtnText: { color: '#9C27B0', fontSize: 13, fontWeight: 'bold' },
  galleryOverlay: { flex: 1, backgroundColor: '#000', justifyContent: 'center' },
  galleryHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, paddingTop: 40 },
  galleryTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  galleryImage: { width: '100%', height: 350 },
  galleryNav: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 24, paddingVertical: 16 },
  galleryNavBtn: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  galleryCount: { color: '#888', fontSize: 14 },
  thumbRow: { paddingHorizontal: 16 },
  thumb: { width: 70, height: 50, borderRadius: 8, marginRight: 8, borderWidth: 2, borderColor: 'transparent' },
  thumbActive: { borderColor: '#9C27B0' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
