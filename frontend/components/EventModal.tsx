import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface EventChoice {
  id: string;
  text: string;
  consequences: { money?: number; xp?: number };
}

interface GameEvent {
  id: string;
  type: string;
  title: string;
  description: string;
  emoji: string;
  color: string;
  choices: EventChoice[];
  ai_generated?: boolean;
  difficulty?: string;
}

interface EventResult {
  success: boolean;
  choice: string;
  consequences: { money: number; xp: number };
  message: string;
}

interface EventModalProps {
  visible: boolean;
  event: GameEvent | null;
  onChoose: (eventId: string, choiceId: string) => Promise<EventResult | null>;
  onClose: () => void;
  loading?: boolean;
}

const TYPE_ICONS: Record<string, string> = {
  opportunity: 'diamond',
  crisis: 'warning',
  challenge: 'flag',
  luck: 'leaf',
  decision: 'scale',
  market: 'stats-chart',
};

export default function EventModal({ visible, event, onChoose, onClose, loading }: EventModalProps) {
  const { t, formatMoney } = useLanguage();
  const { colors } = useTheme();
  const [choosing, setChoosing] = useState<string | null>(null);
  const [result, setResult] = useState<EventResult | null>(null);

  if (!event) return null;

  const handleChoice = async (choiceId: string) => {
    setChoosing(choiceId);
    try {
      const res = await onChoose(event.id, choiceId);
      if (res) {
        setResult(res);
      }
    } catch (e) {
      console.log('Event choice error:', e);
    } finally {
      setChoosing(null);
    }
  };

  const handleDismiss = () => {
    setResult(null);
    onClose();
  };

  const iconName = TYPE_ICONS[event.type] || 'flash';

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleDismiss}
    >
      <View style={styles.overlay}>
        <View style={[styles.container, { borderColor: event.color + '60', backgroundColor: colors.card }]}>
          {/* Header with type badge */}
          <View style={[styles.header, { backgroundColor: event.color + '20' }]}>
            <View style={[styles.iconCircle, { backgroundColor: event.color + '30' }]}>
              <Text style={styles.emoji}>{event.emoji}</Text>
            </View>
            <View style={styles.headerText}>
              <View style={styles.typeBadgeRow}>
                <View style={[styles.typeBadge, { backgroundColor: event.color + '30' }]}>
                  <Text style={[styles.typeBadgeText, { color: event.color }]}>
                    {event.type === 'opportunity' ? '💎 Oportunidade' :
                     event.type === 'crisis' ? '⚠️ Crise' :
                     event.type === 'challenge' ? '🎯 Desafio' :
                     event.type === 'luck' ? '🍀 Sorte' :
                     event.type === 'decision' ? '⚖️ Decisão' :
                     event.type === 'market' ? '📊 Mercado' : event.type}
                  </Text>
                </View>
                {event.ai_generated && (
                  <View style={styles.aiBadge}>
                    <Ionicons name="sparkles" size={10} color="#FFD700" />
                    <Text style={styles.aiBadgeText}>IA</Text>
                  </View>
                )}
              </View>
              <Text style={styles.title}>{event.title}</Text>
            </View>
          </View>

          {/* Description */}
          <View style={styles.body}>
            <Text style={styles.description}>{event.description}</Text>

            {/* Result screen */}
            {result ? (
              <View style={styles.resultContainer}>
                <View style={[styles.resultBanner, {
                  backgroundColor: result.consequences.money >= 0 ? 'rgba(76,175,80,0.15)' : 'rgba(244,67,54,0.15)',
                }]}>
                  <Text style={styles.resultTitle}>
                    {result.consequences.money >= 0 ? '✅' : '⚠️'} Resultado
                  </Text>
                  <Text style={styles.resultChoice}>
                    Escolha: {result.choice}
                  </Text>
                  <View style={styles.resultRow}>
                    <View style={styles.resultItem}>
                      <Ionicons
                        name={result.consequences.money >= 0 ? 'arrow-up-circle' : 'arrow-down-circle'}
                        size={24}
                        color={result.consequences.money >= 0 ? '#4CAF50' : '#F44336'}
                      />
                      <Text style={[styles.resultValue, {
                        color: result.consequences.money >= 0 ? '#4CAF50' : '#F44336',
                      }]}>
                        {result.consequences.money >= 0 ? '+' : ''}{formatMoney(result.consequences.money)}
                      </Text>
                      <Text style={styles.resultLabel}>Dinheiro</Text>
                    </View>
                    <View style={styles.resultItem}>
                      <Ionicons
                        name={result.consequences.xp >= 0 ? 'star' : 'star-outline'}
                        size={24}
                        color={result.consequences.xp >= 0 ? '#FFD700' : '#F44336'}
                      />
                      <Text style={[styles.resultValue, {
                        color: result.consequences.xp >= 0 ? '#FFD700' : '#F44336',
                      }]}>
                        {result.consequences.xp >= 0 ? '+' : ''}{result.consequences.xp} XP
                      </Text>
                      <Text style={styles.resultLabel}>Experiência</Text>
                    </View>
                  </View>
                </View>
                <TouchableOpacity
                  style={[styles.closeBtn, { backgroundColor: event.color }]}
                  onPress={handleDismiss}
                  activeOpacity={0.8}
                >
                  <Text style={styles.closeBtnText}>Continuar</Text>
                </TouchableOpacity>
              </View>
            ) : (
              /* Choices */
              <View style={styles.choicesContainer}>
                <Text style={styles.choicesLabel}>O que você faz?</Text>
                {event.choices.map((choice, index) => {
                  const money = choice.consequences?.money || 0;
                  const xp = choice.consequences?.xp || 0;
                  const isChoosing = choosing === choice.id;

                  return (
                    <TouchableOpacity
                      key={choice.id}
                      style={[
                        styles.choiceBtn,
                        isChoosing && styles.choiceBtnActive,
                        choosing && !isChoosing && styles.choiceBtnDisabled,
                      ]}
                      onPress={() => handleChoice(choice.id)}
                      disabled={!!choosing}
                      activeOpacity={0.7}
                    >
                      <View style={styles.choiceContent}>
                        <View style={styles.choiceNumberBg}>
                          <Text style={styles.choiceNumber}>{index + 1}</Text>
                        </View>
                        <View style={styles.choiceTextContainer}>
                          <Text style={styles.choiceText}>{choice.text}</Text>
                          <View style={styles.consequenceRow}>
                            {money !== 0 && (
                              <View style={[
                                styles.consequencePill,
                                { backgroundColor: money > 0 ? 'rgba(76,175,80,0.15)' : 'rgba(244,67,54,0.15)' },
                              ]}>
                                <Text style={{
                                  fontSize: 11,
                                  fontWeight: '700',
                                  color: money > 0 ? '#4CAF50' : '#F44336',
                                }}>
                                  {money > 0 ? '+' : ''}{formatMoney(money)}
                                </Text>
                              </View>
                            )}
                            {xp !== 0 && (
                              <View style={[
                                styles.consequencePill,
                                { backgroundColor: xp > 0 ? 'rgba(255,215,0,0.15)' : 'rgba(244,67,54,0.15)' },
                              ]}>
                                <Text style={{
                                  fontSize: 11,
                                  fontWeight: '700',
                                  color: xp > 0 ? '#FFD700' : '#F44336',
                                }}>
                                  {xp > 0 ? '+' : ''}{xp} XP
                                </Text>
                              </View>
                            )}
                          </View>
                        </View>
                        {isChoosing && (
                          <ActivityIndicator size="small" color="#fff" />
                        )}
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
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  container: {
    width: Math.min(SCREEN_WIDTH - 40, 400),
    backgroundColor: '#1e1e1e',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1.5,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  iconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emoji: {
    fontSize: 26,
  },
  headerText: {
    flex: 1,
  },
  typeBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: 'rgba(255,215,0,0.15)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  aiBadgeText: {
    fontSize: 10,
    color: '#FFD700',
    fontWeight: '700',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  body: {
    padding: 16,
    paddingTop: 0,
  },
  description: {
    fontSize: 14,
    color: '#bbb',
    lineHeight: 21,
    marginBottom: 16,
  },
  choicesContainer: {
    gap: 8,
  },
  choicesLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#888',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  choiceBtn: {
    backgroundColor: '#2a2a2a',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },
  choiceBtnActive: {
    borderColor: '#4CAF50',
    backgroundColor: '#2a3a2a',
  },
  choiceBtnDisabled: {
    opacity: 0.4,
  },
  choiceContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  choiceNumberBg: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#3a3a3a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  choiceNumber: {
    color: '#fff',
    fontSize: 13,
    fontWeight: 'bold',
  },
  choiceTextContainer: {
    flex: 1,
    gap: 4,
  },
  choiceText: {
    fontSize: 14,
    color: '#eee',
    fontWeight: '500',
  },
  consequenceRow: {
    flexDirection: 'row',
    gap: 6,
    flexWrap: 'wrap',
  },
  consequencePill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  // Result
  resultContainer: {
    gap: 12,
  },
  resultBanner: {
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    gap: 8,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  resultChoice: {
    fontSize: 13,
    color: '#aaa',
    textAlign: 'center',
  },
  resultRow: {
    flexDirection: 'row',
    gap: 24,
    marginTop: 8,
  },
  resultItem: {
    alignItems: 'center',
    gap: 4,
  },
  resultValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  resultLabel: {
    fontSize: 11,
    color: '#888',
  },
  closeBtn: {
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  closeBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
