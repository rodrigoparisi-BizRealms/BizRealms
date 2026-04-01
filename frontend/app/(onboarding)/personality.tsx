import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const PERSONALITY_QUESTIONS = [
  {
    id: 'ambição',
    question: 'Qual seu nível de ambição?',
    low: 'Prefiro estabilidade',
    high: 'Sempre busco mais',
  },
  {
    id: 'risco',
    question: 'Como você lida com riscos?',
    low: 'Conservador e seguro',
    high: 'Arriscado e ousado',
  },
  {
    id: 'social',
    question: 'Você é mais...',
    low: 'Introspectivo e focado',
    high: 'Social e conectado',
  },
  {
    id: 'analítico',
    question: 'Como você toma decisões?',
    low: 'Intuição e feeling',
    high: 'Análise e dados',
  },
];

export default function PersonalitySelection() {
  const router = useRouter();
  const { token, refreshUser } = useAuth();
  const [personality, setPersonality] = useState({
    ambição: 5,
    risco: 5,
    social: 5,
    analítico: 5,
  });
  const [loading, setLoading] = useState(false);

  const handleSliderChange = (trait: string, value: number) => {
    setPersonality(prev => ({ ...prev, [trait]: value }));
  };

  const handleComplete = async () => {
    if (loading) return; // Prevenir múltiplos cliques
    
    setLoading(true);
    console.log('[Personality] Starting profile completion...');
    
    try {
      // Get stored data
      const avatarColor = await AsyncStorage.getItem('avatar_color') || 'green';
      const avatarIcon = await AsyncStorage.getItem('avatar_icon') || 'person';
      const background = await AsyncStorage.getItem('background') || 'trabalhador';
      const dream = await AsyncStorage.getItem('dream') || 'carreira';

      console.log('[Personality] Sending data:', { avatarColor, avatarIcon, background, dream });

      // Send to backend
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/character/complete-profile`,
        {
          avatar_color: avatarColor,
          avatar_icon: avatarIcon,
          background: background,
          dream: dream,
          personality: personality,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log('[Personality] Profile completed successfully:', response.data);

      // Clear temp storage
      await AsyncStorage.multiRemove(['avatar_color', 'avatar_icon', 'background', 'dream']);
      console.log('[Personality] Temp storage cleared');

      // Refresh user data - this will update onboarding_completed
      console.log('[Personality] Refreshing user data...');
      await refreshUser();
      console.log('[Personality] User data refreshed');

      // Don't navigate here - let index.tsx handle it based on onboarding_completed
      // The refreshUser above will trigger the useEffect in index.tsx
      
      // Show success
      Alert.alert(
        'Personagem Criado! 🎉',
        `Bem-vindo ao Business Empire!\n\nDinheiro inicial: R$ ${response.data.money.toLocaleString('pt-BR')}`,
        [
          {
            text: 'Começar!',
            onPress: () => {
              // Force navigation after user confirms
              router.replace('/(tabs)/home');
            }
          }
        ]
      );
      setLoading(false);
    } catch (error: any) {
      console.error('[Personality] Error completing profile:', error);
      console.error('[Personality] Error details:', error.response?.data);
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao criar personagem');
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={[styles.progressDot, styles.progressDotActive]} />
        </View>

        {/* Header */}
        <Text style={styles.title}>Sua Personalidade</Text>
        <Text style={styles.subtitle}>
          Suas escolhas influenciarão oportunidades e desafios
        </Text>

        {/* Personality Questions */}
        {PERSONALITY_QUESTIONS.map(q => (
          <View key={q.id} style={styles.questionContainer}>
            <Text style={styles.questionText}>{q.question}</Text>
            
            <View style={styles.sliderContainer}>
              <Text style={styles.sliderLabel}>{q.low}</Text>
              <View style={styles.sliderTrack}>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(value => (
                  <TouchableOpacity
                    key={value}
                    style={[
                      styles.sliderDot,
                      personality[q.id as keyof typeof personality] >= value &&
                        styles.sliderDotActive,
                    ]}
                    onPress={() => handleSliderChange(q.id, value)}
                  />
                ))}
              </View>
              <Text style={styles.sliderLabel}>{q.high}</Text>
            </View>

            <Text style={styles.sliderValue}>
              Nível: {personality[q.id as keyof typeof personality]}/10
            </Text>
          </View>
        ))}

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Ionicons name="information-circle" size={20} color="#2196F3" />
          <Text style={styles.infoText}>
            Esses traços afetarão suas oportunidades de trabalho, investimentos e parcerias
            empresariais ao longo do jogo.
          </Text>
        </View>

        {/* Navigation */}
        <View style={styles.navigationContainer}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            disabled={loading}
          >
            <Ionicons name="arrow-back" size={20} color="#888" />
            <Text style={styles.backButtonText}>Voltar</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.completeButton, loading && styles.completeButtonDisabled]}
            onPress={handleComplete}
            disabled={loading}
          >
            <Text style={styles.completeButtonText}>
              {loading ? 'Criando...' : 'Começar Jogo!'}
            </Text>
            <Ionicons name="checkmark-circle" size={20} color="#fff" />
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  content: {
    padding: 24,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 32,
  },
  progressDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#3a3a3a',
  },
  progressDotActive: {
    backgroundColor: '#4CAF50',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    marginBottom: 32,
  },
  questionContainer: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  questionText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  sliderLabel: {
    fontSize: 12,
    color: '#888',
    width: 70,
    textAlign: 'center',
  },
  sliderTrack: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 4,
  },
  sliderDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#3a3a3a',
  },
  sliderDotActive: {
    backgroundColor: '#4CAF50',
  },
  sliderValue: {
    fontSize: 14,
    color: '#4CAF50',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  infoBox: {
    backgroundColor: '#1a2a3a',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#2196F3',
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#aaa',
    lineHeight: 20,
  },
  navigationContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  backButton: {
    flex: 1,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    height: 56,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  backButtonText: {
    color: '#888',
    fontSize: 18,
    fontWeight: 'bold',
  },
  completeButton: {
    flex: 2,
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    height: 56,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  completeButtonDisabled: {
    opacity: 0.6,
  },
  completeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
