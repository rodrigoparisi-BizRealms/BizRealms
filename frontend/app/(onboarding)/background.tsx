import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Background {
  id: string;
  name: string;
  description: string;
  money_bonus: number;
  skill_bonuses: Record<string, number>;
  xp_multiplier: number;
}

export default function BackgroundSelection() {
  const router = useRouter();
  const [backgrounds, setBackgrounds] = useState<Background[]>([]);
  const [selectedBackground, setSelectedBackground] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBackgrounds();
  }, []);

  const loadBackgrounds = async () => {
    try {
      const response = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/character/backgrounds`);
      setBackgrounds(response.data);
      if (response.data.length > 0) {
        setSelectedBackground(response.data[0].id);
      }
    } catch (error) {
      console.error('Error loading backgrounds:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    await AsyncStorage.setItem('background', selectedBackground);
    router.push('/(onboarding)/dream');
  };

  const getBackgroundIcon = (id: string) => {
    const icons: Record<string, any> = {
      'ex-militar': 'shield',
      'universitario': 'school',
      'herdeiro': 'diamond',
      'empreendedor': 'rocket',
      'autodidata': 'book',
      'trabalhador': 'hammer',
    };
    return icons[id] || 'person';
  };

  const formatMoney = (bonus: number) => {
    const total = 1000 + bonus;
    return `$ ${total.toLocaleString('en-US')}`;
  };

  const formatSkills = (skills: Record<string, number>) => {
    return Object.entries(skills)
      .map(([skill, value]) => `+${value} ${skill.charAt(0).toUpperCase() + skill.slice(1)}`)
      .join(', ');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </SafeAreaView>
    );
  }

  const selected = backgrounds.find(b => b.id === selectedBackground);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={styles.progressDot} />
          <View style={styles.progressDot} />
        </View>

        {/* Header */}
        <Text style={styles.title}>Sua História</Text>
        <Text style={styles.subtitle}>De onde você vem? Cada origem traz vantagens únicas</Text>

        {/* Background Cards */}
        {backgrounds.map(background => (
          <TouchableOpacity
            key={background.id}
            style={[
              styles.backgroundCard,
              selectedBackground === background.id && styles.backgroundCardSelected,
            ]}
            onPress={() => setSelectedBackground(background.id)}
          >
            <View style={styles.backgroundHeader}>
              <View
                style={[
                  styles.backgroundIcon,
                  selectedBackground === background.id && styles.backgroundIconSelected,
                ]}
              >
                <Ionicons
                  name={getBackgroundIcon(background.id) as any}
                  size={32}
                  color={selectedBackground === background.id ? '#4CAF50' : '#888'}
                />
              </View>
              <View style={styles.backgroundInfo}>
                <Text style={styles.backgroundName}>{background.name}</Text>
                <Text style={styles.backgroundDescription}>{background.description}</Text>
              </View>
            </View>

            <View style={styles.bonusContainer}>
              <View style={styles.bonusItem}>
                <Ionicons name="cash" size={16} color="#4CAF50" />
                <Text style={styles.bonusText}>Inicial: {formatMoney(background.money_bonus)}</Text>
              </View>
              {Object.keys(background.skill_bonuses).length > 0 && (
                <View style={styles.bonusItem}>
                  <Ionicons name="star" size={16} color="#FF9800" />
                  <Text style={styles.bonusText}>{formatSkills(background.skill_bonuses)}</Text>
                </View>
              )}
              {background.xp_multiplier !== 1.0 && (
                <View style={styles.bonusItem}>
                  <Ionicons name="trending-up" size={16} color="#2196F3" />
                  <Text style={styles.bonusText}>
                    XP: {background.xp_multiplier > 1 ? '+' : ''}
                    {((background.xp_multiplier - 1) * 100).toFixed(0)}%
                  </Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        ))}

        {/* Navigation */}
        <View style={styles.navigationContainer}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={20} color="#888" />
            <Text style={styles.backButtonText}>Voltar</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.nextButton}
            onPress={handleNext}
            disabled={!selectedBackground}
          >
            <Text style={styles.nextButtonText}>Próximo</Text>
            <Ionicons name="arrow-forward" size={20} color="#fff" />
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
  backgroundCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  backgroundCardSelected: {
    borderColor: '#4CAF50',
    backgroundColor: '#2a3a2a',
  },
  backgroundHeader: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  backgroundIcon: {
    width: 60,
    height: 60,
    borderRadius: 12,
    backgroundColor: '#3a3a3a',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  backgroundIconSelected: {
    backgroundColor: '#3a4a3a',
  },
  backgroundInfo: {
    flex: 1,
  },
  backgroundName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  backgroundDescription: {
    fontSize: 14,
    color: '#888',
  },
  bonusContainer: {
    gap: 8,
  },
  bonusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  bonusText: {
    fontSize: 14,
    color: '#aaa',
  },
  navigationContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
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
  nextButton: {
    flex: 2,
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    height: 56,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  nextButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
