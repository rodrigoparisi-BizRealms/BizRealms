import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Polyline } from 'react-native-svg';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface Asset {
  id: string;
  ticker: string;
  name: string;
  category: string;
  base_price: number;
  current_price: number;
  volatility: number;
  daily_change: number;
  daily_change_pct: number;
  description: string;
  currency: string;
  market_cap?: string;
  sector?: string;
  sparkline: number[];
}

interface Holding {
  id: string;
  asset_id: string;
  ticker: string;
  name: string;
  category: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  invested: number;
  current_value: number;
  profit: number;
  profit_pct: number;
}

interface PortfolioSummary {
  total_invested: number;
  total_current_value: number;
  total_profit: number;
  total_profit_pct: number;
  num_positions: number;
}

interface AssetHistory {
  date: string;
  price: number;
  volume: number;
}

type CategoryType = 'all' | 'acoes' | 'crypto' | 'fundos' | 'commodities';
type ViewMode = 'market' | 'portfolio';

const CATEGORIES: { key: CategoryType; label: string; icon: string }[] = [
  { key: 'all', label: 'Todos', icon: 'grid' },
  { key: 'acoes', label: 'Ações', icon: 'trending-up' },
  { key: 'crypto', label: 'Crypto', icon: 'logo-bitcoin' },
  { key: 'fundos', label: 'Fundos', icon: 'business' },
  { key: 'commodities', label: 'Commod.', icon: 'diamond' },
];

function SparklineChart({ data, width, height, color }: { data: number[]; width: number; height: number; color: string }) {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <Svg width={width} height={height}>
      <Polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

function PriceChart({ data, width, height }: { data: AssetHistory[]; width: number; height: number }) {
  if (!data || data.length < 2) return null;

  const prices = data.map(d => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const isPositive = prices[prices.length - 1] >= prices[0];
  const color = isPositive ? '#4CAF50' : '#F44336';

  const points = prices
    .map((value, index) => {
      const x = (index / (prices.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 8) - 4;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <View>
      <Svg width={width} height={height}>
        <Polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </Svg>
      <View style={chartStyles.labels}>
        <Text style={chartStyles.labelText}>R$ {min.toFixed(2)}</Text>
        <Text style={chartStyles.labelText}>R$ {max.toFixed(2)}</Text>
      </View>
    </View>
  );
}

const chartStyles = StyleSheet.create({
  labels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  labelText: {
    fontSize: 10,
    color: '#666',
  },
});

export default function Investments() {
  const { token, refreshUser } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [category, setCategory] = useState<CategoryType>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('market');

  // Trade modal
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('');
  const [trading, setTrading] = useState(false);

  // Detail modal
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailAsset, setDetailAsset] = useState<Asset | null>(null);
  const [detailHistory, setDetailHistory] = useState<AssetHistory[]>([]);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  // Market events
  const [marketEvents, setMarketEvents] = useState<any[]>([]);
  const [triggeringEvent, setTriggeringEvent] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [marketRes, portfolioRes, eventsRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/investments/market`, { headers }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/investments/portfolio`, { headers }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/market/events`, { headers }).catch(() => ({ data: { active_events: [] } })),
      ]);
      setAssets(marketRes.data);
      setHoldings(portfolioRes.data.holdings);
      setSummary(portfolioRes.data.summary);
      setMarketEvents(eventsRes.data.active_events || []);
    } catch (error) {
      console.error('Error loading investments:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    await refreshUser();
    setRefreshing(false);
  };

  const openTradeModal = (asset: Asset, type: 'buy' | 'sell') => {
    setSelectedAsset(asset);
    setTradeType(type);
    setQuantity('');
    setShowTradeModal(true);
  };

  const openDetail = async (asset: Asset) => {
    setDetailAsset(asset);
    setShowDetailModal(true);
    setLoadingDetail(true);

    try {
      const res = await axios.get(
        `${EXPO_PUBLIC_BACKEND_URL}/api/investments/asset/${asset.id}/history`,
        { headers: { Authorization: `Bearer ${token}` }, params: { days: 30 } }
      );
      setDetailHistory(res.data.history);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoadingDetail(false);
    }
  };

  const showAlert = (title: string, msg: string) => {
    if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
    else Alert.alert(title, msg);
  };

  const handleTriggerEvent = async () => {
    setTriggeringEvent(true);
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/market/trigger-event`, {}, { headers: { Authorization: `Bearer ${token}` } });
      showAlert('Evento!', r.data.message);
      await loadData();
    } catch (e: any) {
      showAlert('Aguarde', e.response?.data?.detail || 'Erro');
    } finally { setTriggeringEvent(false); }
  };

  const handleTrade = async () => {
    if (!selectedAsset || !quantity || parseFloat(quantity) <= 0) {
      showAlert('Erro', 'Informe uma quantidade válida');
      return;
    }

    setTrading(true);
    try {
      const endpoint = tradeType === 'buy' ? 'buy' : 'sell';
      const res = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/investments/${endpoint}`,
        { asset_id: selectedAsset.id, quantity: parseFloat(quantity) },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      showAlert(
        tradeType === 'buy' ? 'Compra Realizada!' : 'Venda Realizada!',
        res.data.message + `\n\nNovo saldo: R$ ${res.data.new_balance.toLocaleString('pt-BR')}`
      );

      setShowTradeModal(false);
      await loadData();
      await refreshUser();
    } catch (error: any) {
      showAlert('Erro', error.response?.data?.detail || 'Erro ao realizar operação');
    } finally {
      setTrading(false);
    }
  };

  const getHoldingForAsset = (assetId: string) => {
    return holdings.find(h => h.asset_id === assetId);
  };

  const filteredAssets = category === 'all' ? assets : assets.filter(a => a.category === category);

  const formatCurrency = (val: number) => {
    if (val >= 1000) return `R$ ${val.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    return `R$ ${val.toFixed(2)}`;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Carregando mercado...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Investimentos</Text>
        <Ionicons name="trending-up" size={28} color="#4CAF50" />
      </View>

      {/* View Mode Toggle */}
      <View style={styles.viewToggle}>
        <TouchableOpacity
          style={[styles.viewToggleBtn, viewMode === 'market' && styles.viewToggleActive]}
          onPress={() => setViewMode('market')}
        >
          <Ionicons name="bar-chart" size={18} color={viewMode === 'market' ? '#fff' : '#888'} />
          <Text style={[styles.viewToggleText, viewMode === 'market' && styles.viewToggleTextActive]}>
            Mercado
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.viewToggleBtn, viewMode === 'portfolio' && styles.viewToggleActive]}
          onPress={() => setViewMode('portfolio')}
        >
          <Ionicons name="wallet" size={18} color={viewMode === 'portfolio' ? '#fff' : '#888'} />
          <Text style={[styles.viewToggleText, viewMode === 'portfolio' && styles.viewToggleTextActive]}>
            Portfólio
          </Text>
          {holdings.length > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{holdings.length}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* ===== MARKET VIEW ===== */}
        {viewMode === 'market' && (
          <>
            {/* Portfolio Summary (compact) */}
            {summary && summary.num_positions > 0 && (
              <TouchableOpacity style={styles.miniPortfolio} onPress={() => setViewMode('portfolio')}>
                <View>
                  <Text style={styles.miniPortfolioLabel}>Meu Portfólio</Text>
                  <Text style={styles.miniPortfolioValue}>
                    {formatCurrency(summary.total_current_value)}
                  </Text>
                </View>
                <View style={styles.miniPortfolioRight}>
                  <Text style={[
                    styles.miniPortfolioProfit,
                    { color: summary.total_profit >= 0 ? '#4CAF50' : '#F44336' }
                  ]}>
                    {summary.total_profit >= 0 ? '+' : ''}{formatCurrency(summary.total_profit)}
                    {' '}({summary.total_profit_pct >= 0 ? '+' : ''}{summary.total_profit_pct.toFixed(1)}%)
                  </Text>
                  <Ionicons name="chevron-forward" size={20} color="#888" />
                </View>
              </TouchableOpacity>
            )}

            {/* Market Events Banner */}
            {marketEvents.length > 0 && (
              <View style={styles.eventsBanner}>
                {marketEvents.map((ev: any) => {
                  const hrs = Math.floor((ev.seconds_remaining || 0) / 3600);
                  const mins = Math.floor(((ev.seconds_remaining || 0) % 3600) / 60);
                  return (
                    <View key={ev.id} style={[styles.eventCard, { borderLeftColor: ev.color || '#4CAF50', borderLeftWidth: 4 }]}>
                      <View style={styles.eventRow}>
                        <Ionicons name={(ev.icon || 'flash') as any} size={20} color={ev.color || '#4CAF50'} />
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.eventTitle, { color: ev.color || '#4CAF50' }]}>{ev.title}</Text>
                          <Text style={styles.eventDesc}>{ev.description}</Text>
                        </View>
                        <Text style={styles.eventTimer}>{hrs}h{mins.toString().padStart(2, '0')}m</Text>
                      </View>
                      <View style={styles.eventEffects}>
                        {Object.entries(ev.effect || {}).map(([cat, mult]: [string, any]) => (
                          <View key={cat} style={[styles.effectChip, { backgroundColor: mult > 1 ? '#4CAF5020' : '#F4433620' }]}>
                            <Text style={[styles.effectText, { color: mult > 1 ? '#4CAF50' : '#F44336' }]}>
                              {cat.toUpperCase()} {mult > 1 ? '+' : ''}{((mult - 1) * 100).toFixed(0)}%
                            </Text>
                          </View>
                        ))}
                      </View>
                    </View>
                  );
                })}
              </View>
            )}
            {marketEvents.length === 0 && (
              <TouchableOpacity style={styles.triggerEventBtn} onPress={handleTriggerEvent} disabled={triggeringEvent}>
                <Ionicons name="newspaper" size={18} color="#FFD700" />
                <Text style={styles.triggerEventText}>{triggeringEvent ? 'Aguarde...' : 'Gerar Evento de Mercado'}</Text>
              </TouchableOpacity>
            )}

            {/* Category Tabs */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
              <View style={styles.categoryRow}>
                {CATEGORIES.map(cat => (
                  <TouchableOpacity
                    key={cat.key}
                    style={[styles.categoryTab, category === cat.key && styles.categoryTabActive]}
                    onPress={() => setCategory(cat.key)}
                  >
                    <Ionicons
                      name={cat.icon as any}
                      size={16}
                      color={category === cat.key ? '#fff' : '#888'}
                    />
                    <Text style={[
                      styles.categoryTabText,
                      category === cat.key && styles.categoryTabTextActive
                    ]}>
                      {cat.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>

            {/* Asset List */}
            {filteredAssets.map(asset => {
              const holding = getHoldingForAsset(asset.id);
              const isPositive = asset.daily_change_pct >= 0;
              const sparkColor = isPositive ? '#4CAF50' : '#F44336';

              return (
                <TouchableOpacity
                  key={asset.id}
                  style={styles.assetCard}
                  onPress={() => openDetail(asset)}
                  activeOpacity={0.7}
                >
                  <View style={styles.assetLeft}>
                    <View style={styles.assetTickerRow}>
                      <Text style={styles.assetTicker}>{asset.ticker}</Text>
                      {holding && (
                        <View style={styles.holdingBadge}>
                          <Text style={styles.holdingBadgeText}>{holding.quantity.toFixed(holding.quantity >= 1 ? 0 : 4)}</Text>
                        </View>
                      )}
                    </View>
                    <Text style={styles.assetName} numberOfLines={1}>{asset.name}</Text>
                    {asset.sector && (
                      <Text style={styles.assetSector}>{asset.sector}</Text>
                    )}
                  </View>

                  <View style={styles.assetCenter}>
                    <SparklineChart
                      data={asset.sparkline}
                      width={60}
                      height={30}
                      color={sparkColor}
                    />
                  </View>

                  <View style={styles.assetRight}>
                    <Text style={styles.assetPrice}>{formatCurrency(asset.current_price)}</Text>
                    <View style={[styles.changeBadge, { backgroundColor: isPositive ? '#1a3a1a' : '#3a1a1a' }]}>
                      <Ionicons
                        name={isPositive ? 'caret-up' : 'caret-down'}
                        size={12}
                        color={isPositive ? '#4CAF50' : '#F44336'}
                      />
                      <Text style={[styles.changeText, { color: isPositive ? '#4CAF50' : '#F44336' }]}>
                        {isPositive ? '+' : ''}{asset.daily_change_pct.toFixed(2)}%
                      </Text>
                    </View>
                  </View>
                </TouchableOpacity>
              );
            })}
          </>
        )}

        {/* ===== PORTFOLIO VIEW ===== */}
        {viewMode === 'portfolio' && (
          <>
            {/* Summary Card */}
            {summary && (
              <View style={styles.summaryCard}>
                <Text style={styles.summaryLabel}>Valor Total do Portfólio</Text>
                <Text style={styles.summaryValue}>{formatCurrency(summary.total_current_value)}</Text>
                <View style={styles.summaryRow}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryItemLabel}>Investido</Text>
                    <Text style={styles.summaryItemValue}>{formatCurrency(summary.total_invested)}</Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryItemLabel}>Lucro/Prejuízo</Text>
                    <Text style={[
                      styles.summaryItemValue,
                      { color: summary.total_profit >= 0 ? '#4CAF50' : '#F44336' }
                    ]}>
                      {summary.total_profit >= 0 ? '+' : ''}{formatCurrency(summary.total_profit)}
                      {' '}({summary.total_profit_pct >= 0 ? '+' : ''}{summary.total_profit_pct.toFixed(1)}%)
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {/* Holdings */}
            {holdings.length === 0 ? (
              <View style={styles.emptyPortfolio}>
                <Ionicons name="pie-chart-outline" size={64} color="#555" />
                <Text style={styles.emptyTitle}>Portfólio Vazio</Text>
                <Text style={styles.emptySubtext}>
                  Comece a investir comprando ações, cripto ou fundos no mercado
                </Text>
                <TouchableOpacity style={styles.goToMarket} onPress={() => setViewMode('market')}>
                  <Text style={styles.goToMarketText}>Ir para o Mercado</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                <Text style={styles.holdingsTitle}>Minhas Posições ({holdings.length})</Text>
                {holdings.map(holding => {
                  const isProfit = holding.profit >= 0;
                  const asset = assets.find(a => a.id === holding.asset_id);

                  return (
                    <View key={holding.id} style={styles.holdingCard}>
                      <View style={styles.holdingHeader}>
                        <View>
                          <Text style={styles.holdingTicker}>{holding.ticker}</Text>
                          <Text style={styles.holdingName}>{holding.name}</Text>
                        </View>
                        <View style={styles.holdingValues}>
                          <Text style={styles.holdingCurrentValue}>
                            {formatCurrency(holding.current_value)}
                          </Text>
                          <Text style={[
                            styles.holdingProfit,
                            { color: isProfit ? '#4CAF50' : '#F44336' }
                          ]}>
                            {isProfit ? '+' : ''}{formatCurrency(holding.profit)}
                            {' '}({isProfit ? '+' : ''}{holding.profit_pct.toFixed(1)}%)
                          </Text>
                        </View>
                      </View>

                      <View style={styles.holdingDetails}>
                        <View style={styles.holdingDetail}>
                          <Text style={styles.detailLabel}>Quantidade</Text>
                          <Text style={styles.detailValue}>
                            {holding.quantity >= 1 ? holding.quantity.toFixed(0) : holding.quantity.toFixed(4)}
                          </Text>
                        </View>
                        <View style={styles.holdingDetail}>
                          <Text style={styles.detailLabel}>Preço Médio</Text>
                          <Text style={styles.detailValue}>{formatCurrency(holding.avg_price)}</Text>
                        </View>
                        <View style={styles.holdingDetail}>
                          <Text style={styles.detailLabel}>Preço Atual</Text>
                          <Text style={styles.detailValue}>{formatCurrency(holding.current_price)}</Text>
                        </View>
                      </View>

                      <View style={styles.holdingActions}>
                        {asset && (
                          <>
                            <TouchableOpacity
                              style={styles.buyBtn}
                              onPress={() => openTradeModal(asset, 'buy')}
                            >
                              <Text style={styles.buyBtnText}>Comprar</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                              style={styles.sellBtn}
                              onPress={() => openTradeModal(asset, 'sell')}
                            >
                              <Text style={styles.sellBtnText}>Vender</Text>
                            </TouchableOpacity>
                          </>
                        )}
                      </View>
                    </View>
                  );
                })}
              </>
            )}
          </>
        )}
      </ScrollView>

      {/* ===== ASSET DETAIL MODAL ===== */}
      <Modal
        visible={showDetailModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowDetailModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.detailModal}>
            {detailAsset && (
              <>
                <View style={styles.detailHeader}>
                  <View>
                    <Text style={styles.detailTicker}>{detailAsset.ticker}</Text>
                    <Text style={styles.detailName}>{detailAsset.name}</Text>
                  </View>
                  <TouchableOpacity onPress={() => setShowDetailModal(false)}>
                    <Ionicons name="close" size={28} color="#fff" />
                  </TouchableOpacity>
                </View>

                <View style={styles.detailPriceRow}>
                  <Text style={styles.detailPrice}>{formatCurrency(detailAsset.current_price)}</Text>
                  <View style={[
                    styles.changeBadgeLarge,
                    { backgroundColor: detailAsset.daily_change_pct >= 0 ? '#1a3a1a' : '#3a1a1a' }
                  ]}>
                    <Ionicons
                      name={detailAsset.daily_change_pct >= 0 ? 'caret-up' : 'caret-down'}
                      size={16}
                      color={detailAsset.daily_change_pct >= 0 ? '#4CAF50' : '#F44336'}
                    />
                    <Text style={[
                      styles.changeTextLarge,
                      { color: detailAsset.daily_change_pct >= 0 ? '#4CAF50' : '#F44336' }
                    ]}>
                      {detailAsset.daily_change_pct >= 0 ? '+' : ''}{detailAsset.daily_change_pct.toFixed(2)}%
                    </Text>
                  </View>
                </View>

                {/* Chart */}
                <View style={styles.chartContainer}>
                  <Text style={styles.chartTitle}>Últimos 30 dias</Text>
                  {loadingDetail ? (
                    <ActivityIndicator size="small" color="#4CAF50" />
                  ) : (
                    <PriceChart
                      data={detailHistory}
                      width={SCREEN_WIDTH - 80}
                      height={120}
                    />
                  )}
                </View>

                {/* Info */}
                <View style={styles.detailInfoGrid}>
                  {detailAsset.sector && (
                    <View style={styles.detailInfoItem}>
                      <Text style={styles.detailInfoLabel}>Setor</Text>
                      <Text style={styles.detailInfoValue}>{detailAsset.sector}</Text>
                    </View>
                  )}
                  {detailAsset.market_cap && (
                    <View style={styles.detailInfoItem}>
                      <Text style={styles.detailInfoLabel}>Market Cap</Text>
                      <Text style={styles.detailInfoValue}>{detailAsset.market_cap}</Text>
                    </View>
                  )}
                  <View style={styles.detailInfoItem}>
                    <Text style={styles.detailInfoLabel}>Volatilidade</Text>
                    <Text style={styles.detailInfoValue}>{detailAsset.volatility.toFixed(1)}%</Text>
                  </View>
                  <View style={styles.detailInfoItem}>
                    <Text style={styles.detailInfoLabel}>Categoria</Text>
                    <Text style={styles.detailInfoValue}>
                      {detailAsset.category === 'acoes' ? 'Ações' :
                       detailAsset.category === 'crypto' ? 'Cripto' :
                       detailAsset.category === 'fundos' ? 'Fundos' : 'Commodities'}
                    </Text>
                  </View>
                </View>

                <Text style={styles.detailDescription}>{detailAsset.description}</Text>

                {/* Trade Buttons */}
                <View style={styles.detailButtons}>
                  <TouchableOpacity
                    style={styles.detailBuyBtn}
                    onPress={() => { setShowDetailModal(false); openTradeModal(detailAsset, 'buy'); }}
                  >
                    <Ionicons name="add-circle" size={20} color="#fff" />
                    <Text style={styles.detailBuyText}>Comprar</Text>
                  </TouchableOpacity>
                  {getHoldingForAsset(detailAsset.id) && (
                    <TouchableOpacity
                      style={styles.detailSellBtn}
                      onPress={() => { setShowDetailModal(false); openTradeModal(detailAsset, 'sell'); }}
                    >
                      <Ionicons name="remove-circle" size={20} color="#F44336" />
                      <Text style={styles.detailSellText}>Vender</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>

      {/* ===== TRADE MODAL ===== */}
      <Modal
        visible={showTradeModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowTradeModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalOverlay}
        >
          <View style={styles.tradeModal}>
            {selectedAsset && (
              <>
                <View style={styles.tradeHeader}>
                  <Text style={styles.tradeTitle}>
                    {tradeType === 'buy' ? 'Comprar' : 'Vender'} {selectedAsset.ticker}
                  </Text>
                  <TouchableOpacity onPress={() => setShowTradeModal(false)}>
                    <Ionicons name="close" size={28} color="#fff" />
                  </TouchableOpacity>
                </View>

                <View style={styles.tradeInfo}>
                  <Text style={styles.tradeAssetName}>{selectedAsset.name}</Text>
                  <Text style={styles.tradePrice}>
                    Preço atual: {formatCurrency(selectedAsset.current_price)}
                  </Text>
                  {tradeType === 'sell' && getHoldingForAsset(selectedAsset.id) && (
                    <Text style={styles.tradeAvailable}>
                      Disponível: {getHoldingForAsset(selectedAsset.id)!.quantity.toFixed(
                        getHoldingForAsset(selectedAsset.id)!.quantity >= 1 ? 0 : 4
                      )} unidades
                    </Text>
                  )}
                </View>

                <Text style={styles.tradeLabel}>Quantidade</Text>
                <TextInput
                  style={styles.tradeInput}
                  placeholder="0"
                  placeholderTextColor="#555"
                  value={quantity}
                  onChangeText={setQuantity}
                  keyboardType="decimal-pad"
                  autoFocus
                />

                {/* Quick quantity buttons */}
                <View style={styles.quickButtons}>
                  {tradeType === 'buy' ? (
                    <>
                      {[1, 5, 10, 50, 100].map(n => (
                        <TouchableOpacity
                          key={n}
                          style={styles.quickBtn}
                          onPress={() => setQuantity(String(n))}
                        >
                          <Text style={styles.quickBtnText}>{n}</Text>
                        </TouchableOpacity>
                      ))}
                    </>
                  ) : (
                    <>
                      {getHoldingForAsset(selectedAsset.id) && (
                        <>
                          {[0.25, 0.5, 0.75, 1].map(pct => {
                            const h = getHoldingForAsset(selectedAsset.id)!;
                            const qty = h.quantity * pct;
                            return (
                              <TouchableOpacity
                                key={pct}
                                style={styles.quickBtn}
                                onPress={() => setQuantity(qty.toFixed(qty >= 1 ? 0 : 4))}
                              >
                                <Text style={styles.quickBtnText}>{pct * 100}%</Text>
                              </TouchableOpacity>
                            );
                          })}
                        </>
                      )}
                    </>
                  )}
                </View>

                {quantity && parseFloat(quantity) > 0 && (
                  <View style={styles.tradeSummary}>
                    <Text style={styles.tradeSummaryLabel}>Total</Text>
                    <Text style={styles.tradeSummaryValue}>
                      {formatCurrency(selectedAsset.current_price * parseFloat(quantity))}
                    </Text>
                  </View>
                )}

                <TouchableOpacity
                  style={[
                    styles.tradeConfirmBtn,
                    tradeType === 'sell' && styles.tradeConfirmSell,
                    trading && styles.buttonDisabled,
                  ]}
                  onPress={handleTrade}
                  disabled={trading}
                >
                  {trading ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <Text style={styles.tradeConfirmText}>
                      {tradeType === 'buy' ? 'Confirmar Compra' : 'Confirmar Venda'}
                    </Text>
                  )}
                </TouchableOpacity>
              </>
            )}
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    padding: 16, borderBottomWidth: 1, borderBottomColor: '#2a2a2a',
  },
  title: { fontSize: 28, fontWeight: 'bold', color: '#fff' },
  content: { padding: 16, paddingBottom: 32 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadingText: { color: '#888', fontSize: 16 },

  // View Toggle
  viewToggle: {
    flexDirection: 'row', marginHorizontal: 16, marginTop: 12, gap: 8,
  },
  viewToggleBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingVertical: 10, borderRadius: 10, backgroundColor: '#2a2a2a', gap: 6,
  },
  viewToggleActive: { backgroundColor: '#4CAF50' },
  viewToggleText: { color: '#888', fontSize: 14, fontWeight: 'bold' },
  viewToggleTextActive: { color: '#fff' },
  badge: {
    backgroundColor: '#FF6B6B', borderRadius: 10, paddingHorizontal: 6,
    paddingVertical: 1, marginLeft: 4,
  },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },

  // Mini Portfolio
  miniPortfolio: {
    backgroundColor: '#2a3a2a', borderRadius: 12, padding: 16, marginBottom: 16,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    borderWidth: 1, borderColor: '#4CAF50',
  },
  miniPortfolioLabel: { color: '#888', fontSize: 12, marginBottom: 4 },
  miniPortfolioValue: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  miniPortfolioRight: { alignItems: 'flex-end', flexDirection: 'row', gap: 8 },
  miniPortfolioProfit: { fontSize: 13, fontWeight: 'bold' },

  // Categories
  categoryScroll: { marginBottom: 16, marginTop: 4 },
  categoryRow: { flexDirection: 'row', gap: 8, paddingVertical: 4 },
  categoryTab: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14,
    paddingVertical: 8, borderRadius: 20, backgroundColor: '#2a2a2a', gap: 6,
  },
  categoryTabActive: { backgroundColor: '#4CAF50' },
  categoryTabText: { color: '#888', fontSize: 13, fontWeight: 'bold' },
  categoryTabTextActive: { color: '#fff' },

  // Asset Card
  assetCard: {
    backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16,
    flexDirection: 'row', alignItems: 'center', marginBottom: 10,
  },
  assetLeft: { flex: 1 },
  assetTickerRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  assetTicker: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  holdingBadge: {
    backgroundColor: '#4CAF50', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2,
  },
  holdingBadgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  assetName: { fontSize: 12, color: '#888', marginTop: 2, maxWidth: 120 },
  assetSector: { fontSize: 10, color: '#666', marginTop: 1 },
  assetCenter: { marginHorizontal: 12 },
  assetRight: { alignItems: 'flex-end' },
  assetPrice: { fontSize: 14, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  changeBadge: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8,
    paddingVertical: 3, borderRadius: 6, gap: 2,
  },
  changeText: { fontSize: 12, fontWeight: 'bold' },

  // Portfolio Summary
  summaryCard: {
    backgroundColor: '#2a2a2a', borderRadius: 16, padding: 20, marginBottom: 20,
  },
  summaryLabel: { color: '#888', fontSize: 14, marginBottom: 4 },
  summaryValue: { color: '#fff', fontSize: 32, fontWeight: 'bold', marginBottom: 16 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between' },
  summaryItem: { flex: 1 },
  summaryItemLabel: { color: '#666', fontSize: 12, marginBottom: 4 },
  summaryItemValue: { color: '#fff', fontSize: 14, fontWeight: 'bold' },

  // Holdings
  holdingsTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginBottom: 16 },
  holdingCard: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, marginBottom: 12 },
  holdingHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  holdingTicker: { fontSize: 18, fontWeight: 'bold', color: '#fff' },
  holdingName: { fontSize: 12, color: '#888', marginTop: 2 },
  holdingValues: { alignItems: 'flex-end' },
  holdingCurrentValue: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  holdingProfit: { fontSize: 13, fontWeight: 'bold', marginTop: 2 },
  holdingDetails: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  holdingDetail: { flex: 1, alignItems: 'center' },
  detailLabel: { fontSize: 11, color: '#666', marginBottom: 4 },
  detailValue: { fontSize: 13, color: '#aaa', fontWeight: 'bold' },
  holdingActions: { flexDirection: 'row', gap: 12 },
  buyBtn: {
    flex: 1, backgroundColor: '#4CAF50', borderRadius: 10,
    paddingVertical: 10, alignItems: 'center',
  },
  buyBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  sellBtn: {
    flex: 1, backgroundColor: '#2a2a2a', borderRadius: 10,
    paddingVertical: 10, alignItems: 'center', borderWidth: 1, borderColor: '#F44336',
  },
  sellBtnText: { color: '#F44336', fontWeight: 'bold', fontSize: 14 },

  // Empty
  emptyPortfolio: { alignItems: 'center', paddingVertical: 48 },
  emptyTitle: { color: '#fff', fontSize: 22, fontWeight: 'bold', marginTop: 16 },
  emptySubtext: { color: '#666', fontSize: 14, textAlign: 'center', marginTop: 8, maxWidth: 280 },
  goToMarket: {
    backgroundColor: '#4CAF50', borderRadius: 12, paddingHorizontal: 24,
    paddingVertical: 12, marginTop: 20,
  },
  goToMarketText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },

  // Detail Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'flex-end' },
  detailModal: {
    backgroundColor: '#1a1a1a', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 24, maxHeight: '90%',
  },
  detailHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16,
  },
  detailTicker: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  detailName: { fontSize: 14, color: '#888', marginTop: 4 },
  detailPriceRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  detailPrice: { fontSize: 28, fontWeight: 'bold', color: '#fff' },
  changeBadgeLarge: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10,
    paddingVertical: 4, borderRadius: 8, gap: 4,
  },
  changeTextLarge: { fontSize: 14, fontWeight: 'bold' },
  chartContainer: { marginBottom: 20 },
  chartTitle: { color: '#888', fontSize: 12, marginBottom: 8 },
  detailInfoGrid: {
    flexDirection: 'row', flexWrap: 'wrap', marginBottom: 16, gap: 8,
  },
  detailInfoItem: {
    backgroundColor: '#2a2a2a', borderRadius: 8, padding: 10, minWidth: '45%', flex: 1,
  },
  detailInfoLabel: { color: '#666', fontSize: 11, marginBottom: 4 },
  detailInfoValue: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  detailDescription: { color: '#888', fontSize: 13, lineHeight: 18, marginBottom: 20 },
  detailButtons: { flexDirection: 'row', gap: 12 },
  detailBuyBtn: {
    flex: 1, backgroundColor: '#4CAF50', borderRadius: 12, padding: 14,
    flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8,
  },
  detailBuyText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  detailSellBtn: {
    flex: 1, backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14,
    flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8,
    borderWidth: 1, borderColor: '#F44336',
  },
  detailSellText: { color: '#F44336', fontWeight: 'bold', fontSize: 16 },

  // Trade Modal
  tradeModal: {
    backgroundColor: '#1a1a1a', borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: 24,
  },
  tradeHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16,
  },
  tradeTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  tradeInfo: { marginBottom: 20 },
  tradeAssetName: { color: '#888', fontSize: 14 },
  tradePrice: { color: '#4CAF50', fontSize: 16, fontWeight: 'bold', marginTop: 4 },
  tradeAvailable: { color: '#FF9800', fontSize: 13, marginTop: 4 },
  tradeLabel: { color: '#888', fontSize: 14, marginBottom: 8 },
  // Market Events
  eventsBanner: { marginBottom: 12, gap: 8 },
  eventCard: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 12 },
  eventRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  eventTitle: { fontSize: 14, fontWeight: 'bold' },
  eventDesc: { color: '#888', fontSize: 11, marginTop: 2 },
  eventTimer: { color: '#888', fontSize: 12, fontWeight: 'bold' },
  eventEffects: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  effectChip: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  effectText: { fontSize: 10, fontWeight: 'bold' },
  triggerEventBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, padding: 12, marginBottom: 12, borderRadius: 10, borderWidth: 1, borderColor: '#FFD70040', backgroundColor: '#2a2a1a' },
  triggerEventText: { color: '#FFD700', fontSize: 13, fontWeight: 'bold' },
  tradeInput: {
    backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16,
    color: '#fff', fontSize: 24, fontWeight: 'bold', textAlign: 'center',
    borderWidth: 1, borderColor: '#3a3a3a',
  },
  quickButtons: { flexDirection: 'row', gap: 8, marginTop: 12, justifyContent: 'center' },
  quickBtn: {
    backgroundColor: '#2a2a2a', borderRadius: 8, paddingHorizontal: 14,
    paddingVertical: 8, borderWidth: 1, borderColor: '#3a3a3a',
  },
  quickBtnText: { color: '#aaa', fontSize: 13, fontWeight: 'bold' },
  tradeSummary: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, marginTop: 16,
  },
  tradeSummaryLabel: { color: '#888', fontSize: 16 },
  tradeSummaryValue: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  tradeConfirmBtn: {
    backgroundColor: '#4CAF50', borderRadius: 12, padding: 16,
    alignItems: 'center', marginTop: 16,
  },
  tradeConfirmSell: { backgroundColor: '#F44336' },
  tradeConfirmText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  buttonDisabled: { opacity: 0.6 },
});
