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

interface Dream {
  id: string;
  name: string;
  description: string;
  suggested_path: string;
}

export default function DreamSelection() {
  const router = useRouter();
  const [dreams, setDreams] = useState<Dream[]>([]);
  const [selectedDream, setSelectedDream] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDreams();
  }, []);

  const loadDreams = async () => {
    try {
      const response = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/character/dreams`);
      setDreams(response.data);
      if (response.data.length > 0) {
        setSelectedDream(response.data[0].id);
      }
    } catch (error) {
      console.error('Error loading dreams:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    await AsyncStorage.setItem('dream', selectedDream);
    router.push('/(onboarding)/personality');
  };

  const getDreamIcon = (id: string) => {
    const icons: Record<string, any> = {
      'carreira': 'briefcase',
      'empreendedor': 'rocket',
      'investidor': 'trending-up',
      'freelancer': 'laptop',
    };
    return icons[id] || 'star';
  };

  const getDreamColor = (id: string) => {
    const colors: Record<string, string> = {
      'carreira': '#2196F3',
      'empreendedor': '#FF9800',
      'investidor': '#4CAF50',
      'freelancer': '#9C27B0',
    };
    return colors[id] || '#4CAF50';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={[styles.progressDot, styles.progressDotActive]} />
          <View style={styles.progressDot} />
        </View>

        {/* Header */}
        <Text style={styles.title}>Seu Sonho</Text>
        <Text style={styles.subtitle}>O que você deseja alcançar?</Text>

        {/* Dream Cards */}
        {dreams.map(dream => (
          <TouchableOpacity
            key={dream.id}
            style={[
              styles.dreamCard,
              selectedDream === dream.id && styles.dreamCardSelected,
            ]}
            onPress={() => setSelectedDream(dream.id)}
          >
            <View
              style={[
                styles.dreamIcon,
                { backgroundColor: getDreamColor(dream.id) + '20' },
                selectedDream === dream.id && styles.dreamIconSelected,
              ]}
            >
              <Ionicons
                name={getDreamIcon(dream.id) as any}
                size={40}
                color={getDreamColor(dream.id)}
              />
            </View>

            <View style={styles.dreamInfo}>
              <Text style={styles.dreamName}>{dream.name}</Text>
              <Text style={styles.dreamDescription}>{dream.description}</Text>
              <View style={styles.pathContainer}>
                <Ionicons name="compass" size={14} color="#888" />
                <Text style={styles.pathText}>{dream.suggested_path}</Text>
              </View>
            </View>

            {selectedDream === dream.id && (
              <Ionicons name="checkmark-circle" size={28} color="#4CAF50" />
            )}
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
            disabled={!selectedDream}
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
  dreamCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  dreamCardSelected: {
    borderColor: '#4CAF50',
    backgroundColor: '#2a3a2a',
  },
  dreamIcon: {
    width: 80,
    height: 80,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  dreamIconSelected: {
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  dreamInfo: {
    flex: 1,
  },
  dreamName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  dreamDescription: {
    fontSize: 14,
    color: '#888',
    marginBottom: 8,
  },
  pathContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
  },
  pathText: {
    fontSize: 12,
    color: '#666',
    flex: 1,
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
