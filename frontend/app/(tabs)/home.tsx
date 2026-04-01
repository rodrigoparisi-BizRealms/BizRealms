import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const getAvatarColor = (color: string) => {
  const colors: Record<string, string> = {
    green: '#4CAF50',
    blue: '#2196F3',
    purple: '#9C27B0',
    orange: '#FF9800',
    red: '#F44336',
    yellow: '#FFC107',
  };
  return colors[color] || '#4CAF50';
};

export default function Home() {
  const { user, token, refreshUser } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/user/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshUser();
    await loadStats();
    setRefreshing(false);
  };

  if (!user || !stats) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.loadingText}>Carregando...</Text>
      </SafeAreaView>
    );
  }

  const levelProgress = (stats.experience_points % 1000) / 10;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            {(user as any).avatar_photo ? (
              <Image
                source={{ uri: (user as any).avatar_photo }}
                style={styles.avatarImage}
              />
            ) : (
              <View
                style={[
                  styles.avatar,
                  { backgroundColor: getAvatarColor(user.avatar_color || 'green') },
                ]}
              >
                <Ionicons
                  name={(user.avatar_icon || 'person') as any}
                  size={32}
                  color="#fff"
                />
              </View>
            )}
            <View>
              <Text style={styles.greeting}>Olá, {user.name}!</Text>
              <Text style={styles.location}>
                <Ionicons name="location" size={16} color="#888" /> {user.location}
              </Text>
            </View>
          </View>
          <View style={styles.levelBadge}>
            <Text style={styles.levelText}>Nível {stats.level}</Text>
          </View>
        </View>

        {/* Money Card */}
        <View style={styles.moneyCard}>
          <Ionicons name="wallet" size={32} color="#4CAF50" />
          <View style={styles.moneyInfo}>
            <Text style={styles.moneyLabel}>Dinheiro</Text>
            <Text style={styles.moneyValue}>
              R$ {user.money.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </Text>
          </View>
        </View>

        {/* Experience Progress */}
        <View style={styles.expCard}>
          <View style={styles.expHeader}>
            <Text style={styles.expLabel}>Experiência</Text>
            <Text style={styles.expValue}>
              {stats.experience_points} / {stats.next_level_exp} XP
            </Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${levelProgress}%` }]} />
          </View>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Ionicons name="school" size={24} color="#2196F3" />
            <Text style={styles.statValue}>{stats.education_count}</Text>
            <Text style={styles.statLabel}>Educação</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="ribbon" size={24} color="#FF9800" />
            <Text style={styles.statValue}>{stats.certification_count}</Text>
            <Text style={styles.statLabel}>Certificações</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="briefcase" size={24} color="#9C27B0" />
            <Text style={styles.statValue}>{stats.work_experience_count}</Text>
            <Text style={styles.statLabel}>Empregos</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="time" size={24} color="#F44336" />
            <Text style={styles.statValue}>{stats.months_experience}</Text>
            <Text style={styles.statLabel}>Meses Exp.</Text>
          </View>
        </View>

        {/* Skills */}
        <View style={styles.skillsCard}>
          <Text style={styles.sectionTitle}>Habilidades</Text>
          {Object.entries(stats.skills).map(([skill, level]: [string, any]) => (
            <View key={skill} style={styles.skillRow}>
              <Text style={styles.skillName}>{skill.charAt(0).toUpperCase() + skill.slice(1)}</Text>
              <View style={styles.skillBar}>
                <View style={[styles.skillFill, { width: `${level * 10}%` }]} />
              </View>
              <Text style={styles.skillLevel}>{level}/10</Text>
            </View>
          ))}
        </View>

        {/* Quick Actions */}
        <View style={styles.actionsSection}>
          <Text style={styles.sectionTitle}>Ações Rápidas</Text>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="add-circle" size={24} color="#4CAF50" />
            <Text style={styles.actionText}>Adicionar Educação</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="ribbon" size={24} color="#FF9800" />
            <Text style={styles.actionText}>Obter Certificação</Text>
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
    padding: 16,
  },
  loadingText: {
    color: '#fff',
    textAlign: 'center',
    marginTop: 32,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarImage: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  location: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  levelBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  levelText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  moneyCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  moneyInfo: {
    marginLeft: 16,
  },
  moneyLabel: {
    color: '#888',
    fontSize: 14,
  },
  moneyValue: {
    color: '#4CAF50',
    fontSize: 28,
    fontWeight: 'bold',
  },
  expCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  expHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  expLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  expValue: {
    color: '#888',
    fontSize: 14,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#3a3a3a',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
    flex: 1,
    minWidth: '46%',
    alignItems: 'center',
  },
  statValue: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  statLabel: {
    color: '#888',
    fontSize: 12,
    marginTop: 4,
  },
  skillsCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  skillRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  skillName: {
    color: '#fff',
    width: 120,
    fontSize: 14,
  },
  skillBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#3a3a3a',
    borderRadius: 4,
    marginHorizontal: 12,
    overflow: 'hidden',
  },
  skillFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  skillLevel: {
    color: '#888',
    width: 40,
    textAlign: 'right',
  },
  actionsSection: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#3a3a3a',
  },
  actionText: {
    color: '#fff',
    fontSize: 16,
    marginLeft: 12,
  },
});
