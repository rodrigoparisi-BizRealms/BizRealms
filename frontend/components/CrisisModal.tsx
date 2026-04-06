import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface CrisisOption {
  id: string;
  text: string;
  cost_pct: number;
  xp: number;
  risk: number;
  risk_cost_pct?: number;
  lose_company?: boolean;
}

interface Crisis {
  id: string;
  type: string;
  title: string;
  emoji: string;
  color: string;
  description: string;
  severity: string;
  options: CrisisOption[];
  expires_at?: string;
}

interface CrisisResult {
  success: boolean;
  option_chosen: string;
  cost: number;
  risk_triggered: boolean;
  extra_cost: number;
  total_cost: number;
  xp_gained: number;
  lost_company: string | null;
  message: string;
  new_money: number;
}

interface CrisisModalProps {
  visible: boolean;
  crisis: Crisis | null;
  onResolve: (crisisId: string, optionId: string) => Promise<CrisisResult | null>;
  onClose: () => void;
}

const SEVERITY_LABELS: Record<string, { label: string; color: string }> = {
  low: { label: 'Leve', color: '#FF9800' },
  medium: { label: 'Moderada', color: '#F44336' },
  high: { label: 'Grave', color: '#D32F2F' },
  extreme: { label: 'Crítica', color: '#880E4F' },
};

export default function CrisisModal({ visible, crisis, onResolve, onClose }: CrisisModalProps) {
  const { formatMoney } = useLanguage();
  const { colors } = useTheme();
  const [resolving, setResolving] = useState<string | null>(null);
  const [result, setResult] = useState<CrisisResult | null>(null);

  if (!crisis) return null;

  const severity = SEVERITY_LABELS[crisis.severity] || SEVERITY_LABELS.low;

  const handleResolve = async (optionId: string) => {
    setResolving(optionId);
    try {
      const res = await onResolve(crisis.id, optionId);
      if (res) {
        setResult(res);
      }
    } catch (e) {
      console.log('Crisis resolve error:', e);
    } finally {
      setResolving(null);
    }
  };

  const handleDismiss = () => {
    setResult(null);
    onClose();
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={handleDismiss}>
      <View style={styles.overlay}>
        <View style={[styles.container, { borderColor: crisis.color + '80', backgroundColor: colors.card }]}>
          {/* Danger Header */}
          <View style={[styles.header, { backgroundColor: crisis.color + '20' }]}>
            <View style={styles.headerTop}>
              <Text style={styles.emoji}>{crisis.emoji}</Text>
              <View style={[styles.severityBadge, { backgroundColor: severity.color + '30' }]}>
                <View style={[styles.severityDot, { backgroundColor: severity.color }]} />
                <Text style={[styles.severityText, { color: severity.color }]}>{severity.label}</Text>
              </View>
            </View>
            <Text style={styles.title}>{crisis.title}</Text>
            <Text style={styles.subtitle}>CRISE — Resolva em 24h ou sofra penalidades!</Text>
          </View>

          <View style={styles.body}>
            <Text style={styles.description}>{crisis.description}</Text>

            {result ? (
              <View style={styles.resultContainer}>
                <View style={[styles.resultBanner, {
                  backgroundColor: result.risk_triggered ? 'rgba(244,67,54,0.15)' : 'rgba(76,175,80,0.15)',
                }]}>
                  <Text style={styles.resultTitle}>
                    {result.risk_triggered ? '⚠️ O risco se concretizou!' : '✅ Crise Resolvida'}
                  </Text>
                  <Text style={styles.resultChoice}>
                    Escolha: {result.option_chosen}
                  </Text>
                  <View style={styles.resultRow}>
                    <View style={styles.resultItem}>
                      <Ionicons name="arrow-down-circle" size={24} color="#F44336" />
                      <Text style={[styles.resultValue, { color: '#F44336' }]}>
                        -{formatMoney(result.total_cost)}
                      </Text>
                      <Text style={styles.resultLabel}>Custo Total</Text>
                    </View>
                    <View style={styles.resultItem}>
                      <Ionicons name="star" size={24} color="#FFD700" />
                      <Text style={[styles.resultValue, { color: '#FFD700' }]}>
                        +{result.xp_gained} XP
                      </Text>
                      <Text style={styles.resultLabel}>Experiência</Text>
                    </View>
                  </View>
                  {result.lost_company && (
                    <View style={styles.lostCompanyBanner}>
                      <Text style={styles.lostCompanyText}>
                        Empresa perdida: {result.lost_company}
                      </Text>
                    </View>
                  )}
                </View>
                <TouchableOpacity
                  style={[styles.closeBtn, { backgroundColor: crisis.color }]}
                  onPress={handleDismiss}
                  activeOpacity={0.8}
                >
                  <Text style={styles.closeBtnText}>Continuar</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.optionsContainer}>
                <Text style={styles.optionsLabel}>Como resolver?</Text>
                {crisis.options.map((opt, idx) => {
                  const isResolving = resolving === opt.id;
                  const hasRisk = opt.risk > 0;

                  return (
                    <TouchableOpacity
                      key={opt.id}
                      style={[
                        styles.optionBtn,
                        isResolving && styles.optionBtnActive,
                        resolving && !isResolving && styles.optionBtnDisabled,
                      ]}
                      onPress={() => handleResolve(opt.id)}
                      disabled={!!resolving}
                      activeOpacity={0.7}
                    >
                      <View style={styles.optionContent}>
                        <View style={styles.optionNumberBg}>
                          <Text style={styles.optionNumber}>{idx + 1}</Text>
                        </View>
                        <View style={styles.optionTextContainer}>
                          <Text style={styles.optionText}>{opt.text}</Text>
                          <View style={styles.optionTags}>
                            {opt.cost_pct > 0 && (
                              <View style={[styles.tag, { backgroundColor: 'rgba(244,67,54,0.15)' }]}>
                                <Text style={{ fontSize: 10, fontWeight: '700', color: '#F44336' }}>
                                  -{opt.cost_pct}% do saldo
                                </Text>
                              </View>
                            )}
                            {opt.xp > 0 && (
                              <View style={[styles.tag, { backgroundColor: 'rgba(255,215,0,0.15)' }]}>
                                <Text style={{ fontSize: 10, fontWeight: '700', color: '#FFD700' }}>
                                  +{opt.xp} XP
                                </Text>
                              </View>
                            )}
                            {hasRisk && (
                              <View style={[styles.tag, { backgroundColor: 'rgba(255,152,0,0.15)' }]}>
                                <Ionicons name="warning" size={10} color="#FF9800" />
                                <Text style={{ fontSize: 10, fontWeight: '700', color: '#FF9800', marginLeft: 2 }}>
                                  {opt.risk}% risco
                                </Text>
                              </View>
                            )}
                            {opt.lose_company && (
                              <View style={[styles.tag, { backgroundColor: 'rgba(244,67,54,0.2)' }]}>
                                <Text style={{ fontSize: 10, fontWeight: '700', color: '#F44336' }}>
                                  Perde empresa
                                </Text>
                              </View>
                            )}
                          </View>
                        </View>
                        {isResolving && <ActivityIndicator size="small" color="#fff" />}
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  container: {
    width: Math.min(SCREEN_WIDTH - 40, 400),
    backgroundColor: '#1e1e1e',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 2,
  },
  header: {
    padding: 16,
    alignItems: 'center',
    gap: 6,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    width: '100%',
    justifyContent: 'space-between',
  },
  emoji: { fontSize: 36 },
  severityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 5,
  },
  severityDot: { width: 8, height: 8, borderRadius: 4 },
  severityText: { fontSize: 12, fontWeight: '800' },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff', textAlign: 'center' },
  subtitle: { fontSize: 11, color: '#F44336', fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  body: { padding: 16, paddingTop: 0 },
  description: { fontSize: 14, color: '#bbb', lineHeight: 21, marginBottom: 16 },
  optionsContainer: { gap: 8 },
  optionsLabel: { fontSize: 13, fontWeight: '700', color: '#888', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 },
  optionBtn: { backgroundColor: '#2a2a2a', borderRadius: 14, padding: 14, borderWidth: 1, borderColor: '#3a3a3a' },
  optionBtnActive: { borderColor: '#F44336', backgroundColor: '#3a2a2a' },
  optionBtnDisabled: { opacity: 0.4 },
  optionContent: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  optionNumberBg: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#3a3a3a', justifyContent: 'center', alignItems: 'center' },
  optionNumber: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  optionTextContainer: { flex: 1, gap: 4 },
  optionText: { fontSize: 14, color: '#eee', fontWeight: '500' },
  optionTags: { flexDirection: 'row', gap: 5, flexWrap: 'wrap' },
  tag: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 },
  resultContainer: { gap: 12 },
  resultBanner: { borderRadius: 14, padding: 16, alignItems: 'center', gap: 8 },
  resultTitle: { fontSize: 18, fontWeight: 'bold', color: '#fff' },
  resultChoice: { fontSize: 13, color: '#aaa', textAlign: 'center' },
  resultRow: { flexDirection: 'row', gap: 24, marginTop: 8 },
  resultItem: { alignItems: 'center', gap: 4 },
  resultValue: { fontSize: 18, fontWeight: 'bold' },
  resultLabel: { fontSize: 11, color: '#888' },
  lostCompanyBanner: { backgroundColor: 'rgba(244,67,54,0.2)', padding: 8, borderRadius: 8, marginTop: 8 },
  lostCompanyText: { color: '#F44336', fontSize: 12, fontWeight: '700', textAlign: 'center' },
  closeBtn: { borderRadius: 12, padding: 14, alignItems: 'center' },
  closeBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
