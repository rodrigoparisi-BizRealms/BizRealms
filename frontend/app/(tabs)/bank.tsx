import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl,
  Alert, ActivityIndicator, Modal, TextInput, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'expo-router';
import { useSounds } from '../../hooks/useSounds';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const formatMoney = (v: number) => `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const showAlert = (title: string, msg: string) => {
  if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
  else Alert.alert(title, msg);
};

const confirmAction = (title: string, msg: string, onOk: () => void) => {
  if (Platform.OS === 'web') { if (window.confirm(`${title}\n\n${msg}`)) onOk(); }
  else Alert.alert(title, msg, [{ text: 'Cancelar', style: 'cancel' }, { text: 'Confirmar', onPress: onOk }]);
};

const TRIP_ICONS: Record<string, string> = {
  trip_nacional: 'airplane',
  trip_latam: 'earth',
  trip_europa: 'globe',
  trip_mundo: 'planet',
};

export default function Bank() {
  const { token, user, refreshUser } = useAuth();
  const router = useRouter();
  const { play } = useSounds();
  const [bankData, setBankData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'card' | 'loans'>('overview');
  
  // Modals
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [showPayBillModal, setShowPayBillModal] = useState(false);
  const [showLoanModal, setShowLoanModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Form state
  const [purchaseAmount, setPurchaseAmount] = useState('');
  const [purchaseDesc, setPurchaseDesc] = useState('');
  const [payBillAmount, setPayBillAmount] = useState('');
  const [loanAmount, setLoanAmount] = useState('');
  const [loanType, setLoanType] = useState<'small' | 'large'>('small');
  const [loanMonths, setLoanMonths] = useState('12');

  const headers = { Authorization: `Bearer ${token}` };

  const loadBankData = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/account`, { headers });
      setBankData(res.data);
    } catch (e: any) {
      console.error('Bank load error:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadBankData(); }, [loadBankData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshUser();
    await loadBankData();
    setRefreshing(false);
  };

  // Credit Card Purchase
  const handlePurchase = async () => {
    const amount = parseFloat(purchaseAmount);
    if (!amount || amount <= 0) { showAlert('Erro', 'Valor inválido'); return; }
    setActionLoading(true);
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/credit-card/purchase`, {
        amount, description: purchaseDesc || 'Compra no cartão',
      }, { headers });
      showAlert('Compra Realizada!', r.data.message);
      play('purchase');
      setShowPurchaseModal(false);
      setPurchaseAmount(''); setPurchaseDesc('');
      await loadBankData();
    } catch (e: any) {
      showAlert('Erro', e.response?.data?.detail || 'Erro na compra');
    } finally { setActionLoading(false); }
  };

  // Pay Bill
  const handlePayBill = async () => {
    const amount = parseFloat(payBillAmount);
    setActionLoading(true);
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/credit-card/pay-bill`, {
        amount: amount || 0,
      }, { headers });
      showAlert('Fatura Paga!', r.data.message);
      play('success');
      setShowPayBillModal(false);
      setPayBillAmount('');
      await loadBankData(); await refreshUser();
    } catch (e: any) {
      showAlert('Erro', e.response?.data?.detail || 'Erro ao pagar');
    } finally { setActionLoading(false); }
  };

  // Redeem Miles
  const handleRedeemMiles = (tripId: string, tripName: string, milesCost: number) => {
    confirmAction('Resgatar Viagem', `Deseja trocar ${milesCost.toLocaleString('pt-BR')} milhas por "${tripName}"?`, async () => {
      setActionLoading(true);
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/credit-card/redeem-miles`, {
          trip_id: tripId,
        }, { headers });
        showAlert('Viagem Resgatada!', r.data.message);
        play('levelup');
        await loadBankData(); await refreshUser();
      } catch (e: any) {
        showAlert('Erro', e.response?.data?.detail || 'Erro ao resgatar');
      } finally { setActionLoading(false); }
    });
  };

  // Apply for Loan
  const handleApplyLoan = async () => {
    const amount = parseFloat(loanAmount);
    const months = parseInt(loanMonths) || 12;
    if (!amount || amount <= 0) { showAlert('Erro', 'Valor inválido'); return; }
    setActionLoading(true);
    try {
      const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/loan/apply`, {
        amount, type: loanType, months,
      }, { headers });
      showAlert('Empréstimo Aprovado!', r.data.message);
      play('coin');
      setShowLoanModal(false);
      setLoanAmount('');
      await loadBankData(); await refreshUser();
    } catch (e: any) {
      showAlert('Erro', e.response?.data?.detail || 'Erro ao solicitar');
    } finally { setActionLoading(false); }
  };

  // Pay Loan Installment
  const handlePayLoan = (loanId: string, payment: number) => {
    confirmAction('Pagar Parcela', `Pagar parcela de ${formatMoney(payment)}?`, async () => {
      setActionLoading(true);
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/loan/pay`, {
          loan_id: loanId,
        }, { headers });
        showAlert('Parcela Paga!', r.data.message);
        await loadBankData(); await refreshUser();
      } catch (e: any) {
        showAlert('Erro', e.response?.data?.detail || 'Erro ao pagar');
      } finally { setActionLoading(false); }
    });
  };

  // Payoff Loan
  const handlePayoffLoan = (loanId: string, payoffAmount: number) => {
    confirmAction('Quitar Empréstimo', `Quitar empréstimo por ${formatMoney(payoffAmount)}?\n\nVocê economiza com desconto na quitação antecipada!`, async () => {
      setActionLoading(true);
      try {
        const r = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/bank/loan/payoff`, {
          loan_id: loanId,
        }, { headers });
        showAlert('Empréstimo Quitado!', r.data.message);
        await loadBankData(); await refreshUser();
      } catch (e: any) {
        showAlert('Erro', e.response?.data?.detail || 'Erro ao quitar');
      } finally { setActionLoading(false); }
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={s.container}>
        <View style={s.center}>
          <ActivityIndicator size="large" color="#1E88E5" />
          <Text style={s.loadingText}>Carregando banco...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const card = bankData?.credit_card;
  const loans = bankData?.loans || [];
  const balance = bankData?.balance || 0;
  const totalDebt = bankData?.total_debt || 0;
  const trips = bankData?.available_trips || [];
  const loanLimits = bankData?.loan_limits || {};

  return (
    <SafeAreaView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>Banco On-line</Text>
        <Ionicons name="business" size={28} color="#1E88E5" />
      </View>

      {/* Tab Selector */}
      <View style={s.tabRow}>
        {([
          { key: 'overview', icon: 'wallet', label: 'Visão Geral' },
          { key: 'card', icon: 'card', label: 'Cartão' },
          { key: 'loans', icon: 'cash', label: 'Empréstimos' },
        ] as const).map(t => (
          <TouchableOpacity
            key={t.key}
            style={[s.tab, activeTab === t.key && s.tabActive]}
            onPress={() => setActiveTab(t.key)}
          >
            <Ionicons name={t.icon as any} size={18} color={activeTab === t.key ? '#fff' : '#888'} />
            <Text style={[s.tabText, activeTab === t.key && s.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={s.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#1E88E5" />}
      >
        {/* ==================== OVERVIEW TAB ==================== */}
        {activeTab === 'overview' && (
          <>
            {/* Balance Card */}
            <View style={s.balanceCard}>
              <View style={s.balanceHeader}>
                <Ionicons name="wallet" size={24} color="#1E88E5" />
                <Text style={s.balanceLabel}>Saldo Disponível</Text>
              </View>
              <Text style={s.balanceValue}>{formatMoney(balance)}</Text>
              <View style={s.balanceDivider} />
              <View style={s.balanceRow}>
                <View style={s.balanceItem}>
                  <Text style={s.balanceItemLabel}>Dívida Total</Text>
                  <Text style={[s.balanceItemValue, { color: totalDebt > 0 ? '#F44336' : '#4CAF50' }]}>
                    {formatMoney(totalDebt)}
                  </Text>
                </View>
                <View style={s.balanceItem}>
                  <Text style={s.balanceItemLabel}>Patrimônio Líq.</Text>
                  <Text style={[s.balanceItemValue, { color: '#FFD700' }]}>
                    {formatMoney(balance - totalDebt)}
                  </Text>
                </View>
              </View>
            </View>

            {/* Credit Card Summary */}
            {card && (
              <View style={s.cardSummary}>
                <View style={s.cardVisual}>
                  <View style={s.cardChip} />
                  <Text style={s.cardNumber}>{card.card_number}</Text>
                  <View style={s.cardBottom}>
                    <View>
                      <Text style={s.cardLabel}>LIMITE</Text>
                      <Text style={s.cardVal}>{formatMoney(card.limit)}</Text>
                    </View>
                    <View>
                      <Text style={s.cardLabel}>FATURA</Text>
                      <Text style={[s.cardVal, { color: card.balance_used > 0 ? '#FF6B6B' : '#4CAF50' }]}>
                        {formatMoney(card.balance_used || 0)}
                      </Text>
                    </View>
                    <View>
                      <Text style={s.cardLabel}>MILHAS</Text>
                      <Text style={[s.cardVal, { color: '#FFD700' }]}>
                        {(card.miles_points || 0).toLocaleString('pt-BR')}
                      </Text>
                    </View>
                  </View>
                </View>
              </View>
            )}

            {/* Quick Actions */}
            <View style={s.quickActions}>
              <TouchableOpacity style={s.quickBtn} onPress={() => setShowPurchaseModal(true)}>
                <View style={[s.quickIcon, { backgroundColor: '#1E88E520' }]}>
                  <Ionicons name="card" size={22} color="#1E88E5" />
                </View>
                <Text style={s.quickLabel}>Usar Cartão</Text>
              </TouchableOpacity>
              <TouchableOpacity style={s.quickBtn} onPress={() => setShowPayBillModal(true)}>
                <View style={[s.quickIcon, { backgroundColor: '#4CAF5020' }]}>
                  <Ionicons name="checkmark-circle" size={22} color="#4CAF50" />
                </View>
                <Text style={s.quickLabel}>Pagar Fatura</Text>
              </TouchableOpacity>
              <TouchableOpacity style={s.quickBtn} onPress={() => setShowLoanModal(true)}>
                <View style={[s.quickIcon, { backgroundColor: '#FF980020' }]}>
                  <Ionicons name="cash" size={22} color="#FF9800" />
                </View>
                <Text style={s.quickLabel}>Empréstimo</Text>
              </TouchableOpacity>
              <TouchableOpacity style={s.quickBtn} onPress={() => setActiveTab('card')}>
                <View style={[s.quickIcon, { backgroundColor: '#FFD70020' }]}>
                  <Ionicons name="airplane" size={22} color="#FFD700" />
                </View>
                <Text style={s.quickLabel}>Milhas</Text>
              </TouchableOpacity>
            </View>

            {/* Active Loans Summary */}
            {loans.length > 0 && (
              <View style={s.sectionCard}>
                <Text style={s.sectionTitle}>Empréstimos Ativos ({loans.length})</Text>
                {loans.map((loan: any) => (
                  <View key={loan.id} style={s.loanMini}>
                    <View style={{ flex: 1 }}>
                      <Text style={s.loanMiniType}>
                        {loan.type === 'small' ? 'Sem Garantia' : 'Com Garantia'}
                      </Text>
                      <Text style={s.loanMiniAmount}>
                        {formatMoney(loan.remaining_balance)} restante
                      </Text>
                    </View>
                    <Text style={s.loanMiniPayment}>
                      {formatMoney(loan.monthly_payment)}/mês
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}

        {/* ==================== CARD TAB ==================== */}
        {activeTab === 'card' && (
          <>
            {/* Card Visual */}
            {card && (
              <View style={s.cardSummary}>
                <View style={[s.cardVisual, { height: 200 }]}>
                  <View style={s.cardChip} />
                  <Text style={[s.cardNumber, { fontSize: 20 }]}>{card.card_number}</Text>
                  <View style={s.cardBottom}>
                    <View>
                      <Text style={s.cardLabel}>LIMITE TOTAL</Text>
                      <Text style={s.cardVal}>{formatMoney(card.limit)}</Text>
                    </View>
                    <View>
                      <Text style={s.cardLabel}>DISPONÍVEL</Text>
                      <Text style={[s.cardVal, { color: '#4CAF50' }]}>
                        {formatMoney(card.limit - (card.balance_used || 0))}
                      </Text>
                    </View>
                  </View>
                </View>
              </View>
            )}

            {/* Card Actions */}
            <View style={{ flexDirection: 'row', gap: 10, marginBottom: 16 }}>
              <TouchableOpacity
                style={[s.actionBtn, { backgroundColor: '#1E88E5', flex: 1 }]}
                onPress={() => setShowPurchaseModal(true)}
              >
                <Ionicons name="cart" size={18} color="#fff" />
                <Text style={s.actionBtnText}>Usar Cartão</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[s.actionBtn, { backgroundColor: '#4CAF50', flex: 1 }]}
                onPress={() => setShowPayBillModal(true)}
              >
                <Ionicons name="checkmark-circle" size={18} color="#fff" />
                <Text style={s.actionBtnText}>Pagar Fatura</Text>
              </TouchableOpacity>
            </View>

            {/* Fatura info */}
            <View style={s.sectionCard}>
              <Text style={s.sectionTitle}>Fatura Atual</Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <Text style={s.faturaLabel}>Valor usado:</Text>
                <Text style={[s.faturaValue, { color: (card?.balance_used || 0) > 0 ? '#F44336' : '#4CAF50' }]}>
                  {formatMoney(card?.balance_used || 0)}
                </Text>
              </View>
              <View style={{ marginTop: 12 }}>
                <View style={s.progressBg}>
                  <View style={[s.progressFill, {
                    width: `${Math.min(100, ((card?.balance_used || 0) / (card?.limit || 1)) * 100)}%`,
                    backgroundColor: ((card?.balance_used || 0) / (card?.limit || 1)) > 0.8 ? '#F44336' : '#1E88E5',
                  }]} />
                </View>
                <Text style={s.progressLabel}>
                  {Math.round(((card?.balance_used || 0) / (card?.limit || 1)) * 100)}% do limite utilizado
                </Text>
              </View>
            </View>

            {/* Miles & Trips */}
            <View style={s.sectionCard}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={s.sectionTitle}>Programa de Milhas</Text>
                <View style={s.milesBadge}>
                  <Ionicons name="star" size={14} color="#FFD700" />
                  <Text style={s.milesCount}>{(card?.miles_points || 0).toLocaleString('pt-BR')}</Text>
                </View>
              </View>
              <Text style={s.milesHint}>Ganhe 1 milha a cada R$ 1 gasto no cartão</Text>
              {trips.map((trip: any) => {
                const canRedeem = (card?.miles_points || 0) >= trip.miles_cost;
                return (
                  <View key={trip.id} style={s.tripCard}>
                    <View style={s.tripIcon}>
                      <Ionicons name={(TRIP_ICONS[trip.id] || 'airplane') as any} size={24} color="#FFD700" />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={s.tripName}>{trip.name}</Text>
                      <Text style={s.tripDesc}>{trip.description}</Text>
                      <Text style={s.tripMiles}>{trip.miles_cost.toLocaleString('pt-BR')} milhas</Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={s.tripXp}>+{trip.xp_reward.toLocaleString('pt-BR')} XP</Text>
                      <TouchableOpacity
                        style={[s.redeemBtn, !canRedeem && s.disabledBtn]}
                        onPress={() => handleRedeemMiles(trip.id, trip.name, trip.miles_cost)}
                        disabled={!canRedeem || actionLoading}
                      >
                        <Text style={s.redeemText}>{canRedeem ? 'Resgatar' : 'Insuficiente'}</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })}
            </View>
          </>
        )}

        {/* ==================== LOANS TAB ==================== */}
        {activeTab === 'loans' && (
          <>
            {/* Loan Limits Info */}
            <View style={s.sectionCard}>
              <Text style={s.sectionTitle}>Limites de Crédito</Text>
              <View style={s.limitRow}>
                <View style={s.limitItem}>
                  <Ionicons name="document-text" size={24} color="#FF9800" />
                  <Text style={s.limitLabel}>Sem Garantia</Text>
                  <Text style={s.limitValue}>{formatMoney(loanLimits.small_no_guarantee || 0)}</Text>
                  <Text style={s.limitRate}>3.5% ao mês</Text>
                </View>
                <View style={s.limitItem}>
                  <Ionicons name="shield-checkmark" size={24} color="#4CAF50" />
                  <Text style={s.limitLabel}>Com Garantia</Text>
                  <Text style={s.limitValue}>{formatMoney(loanLimits.large_with_guarantee || 0)}</Text>
                  <Text style={s.limitRate}>2% ao mês</Text>
                </View>
              </View>
              <TouchableOpacity
                style={[s.actionBtn, { backgroundColor: '#FF9800', marginTop: 16 }]}
                onPress={() => setShowLoanModal(true)}
              >
                <Ionicons name="add-circle" size={18} color="#fff" />
                <Text style={s.actionBtnText}>Solicitar Empréstimo</Text>
              </TouchableOpacity>
            </View>

            {/* Active Loans */}
            <View style={s.sectionCard}>
              <Text style={s.sectionTitle}>Empréstimos Ativos ({loans.length}/3)</Text>
              {loans.length === 0 ? (
                <View style={s.emptyLoans}>
                  <Ionicons name="checkmark-circle" size={48} color="#4CAF5050" />
                  <Text style={s.emptyLoanText}>Nenhum empréstimo ativo</Text>
                  <Text style={s.emptyLoanSub}>Você está livre de dívidas!</Text>
                </View>
              ) : loans.map((loan: any) => (
                <View key={loan.id} style={s.loanCard}>
                  <View style={s.loanHeader}>
                    <View style={[s.loanTypeBadge, { 
                      backgroundColor: loan.type === 'small' ? '#FF980020' : '#4CAF5020' 
                    }]}>
                      <Ionicons
                        name={loan.type === 'small' ? 'document-text' : 'shield-checkmark'}
                        size={16}
                        color={loan.type === 'small' ? '#FF9800' : '#4CAF50'}
                      />
                      <Text style={[s.loanTypeText, { 
                        color: loan.type === 'small' ? '#FF9800' : '#4CAF50' 
                      }]}>
                        {loan.type === 'small' ? 'Sem Garantia' : 'Com Garantia'}
                      </Text>
                    </View>
                    <Text style={s.loanAmountSmall}>
                      {loan.payments_made}/{loan.months} parcelas
                    </Text>
                  </View>

                  <View style={s.loanInfoRow}>
                    <View>
                      <Text style={s.loanInfoLabel}>Valor Original</Text>
                      <Text style={s.loanInfoValue}>{formatMoney(loan.amount)}</Text>
                    </View>
                    <View>
                      <Text style={s.loanInfoLabel}>Restante</Text>
                      <Text style={[s.loanInfoValue, { color: '#F44336' }]}>
                        {formatMoney(loan.remaining_balance)}
                      </Text>
                    </View>
                    <View>
                      <Text style={s.loanInfoLabel}>Parcela</Text>
                      <Text style={s.loanInfoValue}>{formatMoney(loan.monthly_payment)}</Text>
                    </View>
                  </View>

                  {/* Progress */}
                  <View style={s.loanProgress}>
                    <View style={s.progressBg}>
                      <View style={[s.progressFill, {
                        width: `${(loan.payments_made / loan.months) * 100}%`,
                        backgroundColor: '#4CAF50',
                      }]} />
                    </View>
                    <Text style={s.progressLabel}>
                      {Math.round((loan.payments_made / loan.months) * 100)}% quitado
                    </Text>
                  </View>

                  <View style={{ flexDirection: 'row', gap: 10, marginTop: 12 }}>
                    <TouchableOpacity
                      style={[s.loanBtn, { backgroundColor: '#1E88E5', flex: 1 }]}
                      onPress={() => handlePayLoan(loan.id, loan.monthly_payment)}
                      disabled={actionLoading}
                    >
                      <Text style={s.loanBtnText}>Pagar Parcela</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[s.loanBtn, { backgroundColor: '#4CAF50', flex: 1 }]}
                      onPress={() => handlePayoffLoan(loan.id, loan.discount_payoff || loan.remaining_balance)}
                      disabled={actionLoading}
                    >
                      <Text style={s.loanBtnText}>Quitar Tudo</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
          </>
        )}
      </ScrollView>

      {/* ==================== MODALS ==================== */}

      {/* Purchase Modal */}
      <Modal visible={showPurchaseModal} animationType="slide" transparent onRequestClose={() => setShowPurchaseModal(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>Compra no Cartão</Text>
              <TouchableOpacity onPress={() => setShowPurchaseModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>
            <Text style={s.modalInfo}>
              Disponível: {formatMoney((card?.limit || 0) - (card?.balance_used || 0))}
            </Text>
            <Text style={s.inputLabel}>Valor (R$)</Text>
            <TextInput
              style={s.input}
              placeholder="Ex: 5000"
              placeholderTextColor="#555"
              keyboardType="numeric"
              value={purchaseAmount}
              onChangeText={setPurchaseAmount}
            />
            <Text style={s.inputLabel}>Descrição</Text>
            <TextInput
              style={s.input}
              placeholder="Ex: Compra de equipamento"
              placeholderTextColor="#555"
              value={purchaseDesc}
              onChangeText={setPurchaseDesc}
            />
            <Text style={s.milesPreview}>
              Milhas a ganhar: +{parseInt(purchaseAmount) || 0} milhas
            </Text>
            <TouchableOpacity
              style={[s.modalBtn, actionLoading && s.disabledBtn]}
              onPress={handlePurchase}
              disabled={actionLoading}
            >
              {actionLoading ? <ActivityIndicator color="#fff" /> : (
                <Text style={s.modalBtnText}>Confirmar Compra</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Pay Bill Modal */}
      <Modal visible={showPayBillModal} animationType="slide" transparent onRequestClose={() => setShowPayBillModal(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>Pagar Fatura</Text>
              <TouchableOpacity onPress={() => setShowPayBillModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>
            <Text style={s.modalInfo}>
              Fatura atual: {formatMoney(card?.balance_used || 0)}
            </Text>
            <Text style={s.modalInfo}>
              Seu saldo: {formatMoney(balance)}
            </Text>
            <Text style={s.inputLabel}>Valor a pagar (vazio = total)</Text>
            <TextInput
              style={s.input}
              placeholder="Deixe vazio para pagar tudo"
              placeholderTextColor="#555"
              keyboardType="numeric"
              value={payBillAmount}
              onChangeText={setPayBillAmount}
            />
            <TouchableOpacity
              style={[s.modalBtn, { backgroundColor: '#4CAF50' }, actionLoading && s.disabledBtn]}
              onPress={handlePayBill}
              disabled={actionLoading}
            >
              {actionLoading ? <ActivityIndicator color="#fff" /> : (
                <Text style={s.modalBtnText}>Pagar Fatura</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Loan Modal */}
      <Modal visible={showLoanModal} animationType="slide" transparent onRequestClose={() => setShowLoanModal(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>Solicitar Empréstimo</Text>
              <TouchableOpacity onPress={() => setShowLoanModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <Text style={s.inputLabel}>Tipo de Empréstimo</Text>
            <View style={{ flexDirection: 'row', gap: 10, marginBottom: 16 }}>
              <TouchableOpacity
                style={[s.typeBtn, loanType === 'small' && s.typeBtnActive]}
                onPress={() => setLoanType('small')}
              >
                <Ionicons name="document-text" size={20} color={loanType === 'small' ? '#fff' : '#FF9800'} />
                <Text style={[s.typeBtnText, loanType === 'small' && { color: '#fff' }]}>Sem Garantia</Text>
                <Text style={[s.typeBtnSub, loanType === 'small' && { color: '#ffffffaa' }]}>3.5%/mês • até 24x</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[s.typeBtn, loanType === 'large' && s.typeBtnActiveLarge]}
                onPress={() => setLoanType('large')}
              >
                <Ionicons name="shield-checkmark" size={20} color={loanType === 'large' ? '#fff' : '#4CAF50'} />
                <Text style={[s.typeBtnText, loanType === 'large' && { color: '#fff' }]}>Com Garantia</Text>
                <Text style={[s.typeBtnSub, loanType === 'large' && { color: '#ffffffaa' }]}>2%/mês • até 60x</Text>
              </TouchableOpacity>
            </View>

            <Text style={s.modalInfo}>
              Máximo: {formatMoney(loanType === 'small' ? (loanLimits.small_no_guarantee || 0) : (loanLimits.large_with_guarantee || 0))}
            </Text>

            <Text style={s.inputLabel}>Valor (R$)</Text>
            <TextInput
              style={s.input}
              placeholder="Ex: 20000"
              placeholderTextColor="#555"
              keyboardType="numeric"
              value={loanAmount}
              onChangeText={setLoanAmount}
            />
            <Text style={s.inputLabel}>Parcelas (meses)</Text>
            <TextInput
              style={s.input}
              placeholder="Ex: 12"
              placeholderTextColor="#555"
              keyboardType="numeric"
              value={loanMonths}
              onChangeText={setLoanMonths}
            />

            {loanAmount ? (
              <View style={s.loanPreview}>
                <Text style={s.loanPreviewTitle}>Simulação:</Text>
                <Text style={s.loanPreviewText}>
                  Parcela estimada: {formatMoney(
                    (parseFloat(loanAmount) * Math.pow(1 + (loanType === 'small' ? 0.035 : 0.02), parseInt(loanMonths) || 12)) / (parseInt(loanMonths) || 12)
                  )}
                </Text>
                <Text style={s.loanPreviewText}>
                  Total a pagar: {formatMoney(
                    parseFloat(loanAmount) * Math.pow(1 + (loanType === 'small' ? 0.035 : 0.02), parseInt(loanMonths) || 12)
                  )}
                </Text>
              </View>
            ) : null}

            <TouchableOpacity
              style={[s.modalBtn, { backgroundColor: '#FF9800' }, actionLoading && s.disabledBtn]}
              onPress={handleApplyLoan}
              disabled={actionLoading}
            >
              {actionLoading ? <ActivityIndicator color="#fff" /> : (
                <Text style={s.modalBtnText}>Solicitar Empréstimo</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
  loadingText: { color: '#888', fontSize: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
  backBtn: { padding: 4 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', flex: 1, textAlign: 'center' },
  content: { padding: 16, paddingBottom: 40 },
  // Tabs
  tabRow: { flexDirection: 'row', margin: 16, marginBottom: 0, gap: 8 },
  tab: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderRadius: 10, backgroundColor: '#2a2a2a', gap: 6 },
  tabActive: { backgroundColor: '#1E88E5' },
  tabText: { color: '#888', fontSize: 12, fontWeight: 'bold' },
  tabTextActive: { color: '#fff' },
  // Balance Card
  balanceCard: { backgroundColor: '#1E3A5F', borderRadius: 16, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: '#1E88E540' },
  balanceHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  balanceLabel: { color: '#88AACC', fontSize: 14 },
  balanceValue: { color: '#fff', fontSize: 32, fontWeight: 'bold', marginBottom: 12 },
  balanceDivider: { height: 1, backgroundColor: '#ffffff15', marginBottom: 12 },
  balanceRow: { flexDirection: 'row', justifyContent: 'space-between' },
  balanceItem: { flex: 1 },
  balanceItemLabel: { color: '#88AACC', fontSize: 12 },
  balanceItemValue: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginTop: 4 },
  // Card Visual
  cardSummary: { marginBottom: 16 },
  cardVisual: { backgroundColor: '#1a2a4a', borderRadius: 16, padding: 20, height: 170, justifyContent: 'space-between', borderWidth: 1, borderColor: '#2a4a7a' },
  cardChip: { width: 36, height: 26, backgroundColor: '#FFD70060', borderRadius: 6 },
  cardNumber: { color: '#ffffffcc', fontSize: 17, letterSpacing: 3, fontWeight: '600' },
  cardBottom: { flexDirection: 'row', justifyContent: 'space-between' },
  cardLabel: { color: '#ffffff60', fontSize: 9, marginBottom: 2 },
  cardVal: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  // Quick Actions
  quickActions: { flexDirection: 'row', gap: 10, marginBottom: 16 },
  quickBtn: { flex: 1, alignItems: 'center', backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14, gap: 8 },
  quickIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  quickLabel: { color: '#ccc', fontSize: 11, fontWeight: '600', textAlign: 'center' },
  // Section Cards
  sectionCard: { backgroundColor: '#2a2a2a', borderRadius: 16, padding: 16, marginBottom: 16 },
  sectionTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  // Loan mini
  loanMini: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#333' },
  loanMiniType: { color: '#ccc', fontSize: 14, fontWeight: '600' },
  loanMiniAmount: { color: '#888', fontSize: 12, marginTop: 2 },
  loanMiniPayment: { color: '#FF9800', fontSize: 14, fontWeight: 'bold' },
  // Card Tab
  faturaLabel: { color: '#888', fontSize: 14 },
  faturaValue: { fontSize: 20, fontWeight: 'bold' },
  progressBg: { height: 8, backgroundColor: '#1a1a1a', borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 4 },
  progressLabel: { color: '#666', fontSize: 11, textAlign: 'center', marginTop: 6 },
  // Miles
  milesBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#FFD70020', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  milesCount: { color: '#FFD700', fontSize: 14, fontWeight: 'bold' },
  milesHint: { color: '#666', fontSize: 12, marginBottom: 16 },
  tripCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1a1a1a', borderRadius: 12, padding: 14, marginBottom: 10, gap: 12 },
  tripIcon: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#FFD70015', justifyContent: 'center', alignItems: 'center' },
  tripName: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  tripDesc: { color: '#888', fontSize: 12, marginTop: 2 },
  tripMiles: { color: '#FFD700', fontSize: 12, fontWeight: '600', marginTop: 4 },
  tripXp: { color: '#4CAF50', fontSize: 13, fontWeight: 'bold', marginBottom: 6 },
  redeemBtn: { backgroundColor: '#FFD700', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 6 },
  redeemText: { color: '#000', fontSize: 12, fontWeight: 'bold' },
  // Loans Tab
  limitRow: { flexDirection: 'row', gap: 12 },
  limitItem: { flex: 1, backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16, alignItems: 'center', gap: 8 },
  limitLabel: { color: '#ccc', fontSize: 13, fontWeight: '600' },
  limitValue: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  limitRate: { color: '#888', fontSize: 11 },
  emptyLoans: { alignItems: 'center', paddingVertical: 24, gap: 8 },
  emptyLoanText: { color: '#888', fontSize: 16, fontWeight: '600' },
  emptyLoanSub: { color: '#555', fontSize: 13 },
  loanCard: { backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16, marginBottom: 12 },
  loanHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  loanTypeBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  loanTypeText: { fontSize: 12, fontWeight: 'bold' },
  loanAmountSmall: { color: '#888', fontSize: 12 },
  loanInfoRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  loanInfoLabel: { color: '#666', fontSize: 11 },
  loanInfoValue: { color: '#fff', fontSize: 14, fontWeight: 'bold', marginTop: 2 },
  loanProgress: { marginTop: 4 },
  loanBtn: { borderRadius: 10, padding: 12, alignItems: 'center' },
  loanBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  // Action Buttons
  actionBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 12, padding: 14 },
  actionBtnText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  disabledBtn: { opacity: 0.5 },
  // Modals
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'flex-end' },
  modal: { backgroundColor: '#1a1a1a', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, maxHeight: '90%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modalTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  modalInfo: { color: '#888', fontSize: 14, marginBottom: 8 },
  inputLabel: { color: '#888', fontSize: 14, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 16, color: '#fff', fontSize: 16, borderWidth: 1, borderColor: '#3a3a3a' },
  milesPreview: { color: '#FFD700', fontSize: 13, marginTop: 12, textAlign: 'center' },
  modalBtn: { backgroundColor: '#1E88E5', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 20 },
  modalBtnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  // Loan Modal
  typeBtn: { flex: 1, backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14, alignItems: 'center', gap: 6, borderWidth: 1, borderColor: '#3a3a3a' },
  typeBtnActive: { backgroundColor: '#FF9800', borderColor: '#FF9800' },
  typeBtnActiveLarge: { backgroundColor: '#4CAF50', borderColor: '#4CAF50' },
  typeBtnText: { color: '#ccc', fontSize: 13, fontWeight: 'bold' },
  typeBtnSub: { color: '#666', fontSize: 10 },
  loanPreview: { backgroundColor: '#2a2a2a', borderRadius: 12, padding: 14, marginTop: 16 },
  loanPreviewTitle: { color: '#FF9800', fontSize: 14, fontWeight: 'bold', marginBottom: 6 },
  loanPreviewText: { color: '#ccc', fontSize: 13, marginTop: 4 },
});
