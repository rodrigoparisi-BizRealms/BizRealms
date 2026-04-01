import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Job {
  id: string;
  title: string;
  company: string;
  description: string;
  salary: number;
  location: string;
  requirements: {
    education_level: number;
    experience_months: number;
    skills: Record<string, number>;
  };
}

interface CurrentJob {
  company: string;
  position: string;
  salary: number;
  days_worked: number;
  last_work_date: string | null;
}

interface AdBoost {
  active: boolean;
  multiplier: number;
  ads_watched: number;
  seconds_remaining: number;
}

export default function Jobs() {
  const { token, refreshUser } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [currentJob, setCurrentJob] = useState<CurrentJob | null>(null);
  const [adBoost, setAdBoost] = useState<AdBoost>({ active: false, multiplier: 1, ads_watched: 0, seconds_remaining: 0 });
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [watchingAd, setWatchingAd] = useState(false);
  const [adProgress, setAdProgress] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
    // Update boost timer every second
    const interval = setInterval(() => {
      if (adBoost.active && adBoost.seconds_remaining > 0) {
        setAdBoost(prev => ({
          ...prev,
          seconds_remaining: Math.max(0, prev.seconds_remaining - 1)
        }));
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [jobsRes, currentJobRes, boostRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/jobs`),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/jobs/current`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/ads/current-boost`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setJobs(jobsRes.data);
      setCurrentJob(currentJobRes.data);
      setAdBoost(boostRes.data);
    } catch (error) {
      console.error('Error loading jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleApply = async (jobId: string) => {
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/jobs/apply`,
        { job_id: jobId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert(
        response.data.status === 'accepted' ? 'Aprovado! 🎉' : 'Candidatura Enviada',
        response.data.message + `\n\nCompatibilidade: ${response.data.match_score.toFixed(0)}%`,
        response.data.status === 'accepted'
          ? [
              { text: 'Ver Depois', style: 'cancel' },
              { text: 'Aceitar Vaga', onPress: () => handleAccept(jobId) },
            ]
          : undefined
      );

      await loadData();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao candidatar-se');
    }
  };

  const handleAccept = async (jobId: string) => {
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/jobs/accept`,
        { job_id: jobId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert(
        'Sucesso! 🎊', 
        response.data.message + `\n\nGanho diário: R$ ${response.data.daily_earnings.toFixed(2)}`
      );
      await loadData();
      await refreshUser();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao aceitar vaga');
    }
  };

  const handleCollectEarnings = async () => {
    setWorking(true);
    try {
      const response = await axios.get(
        `${EXPO_PUBLIC_BACKEND_URL}/api/jobs/collect-earnings`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.earnings === 0) {
        Alert.alert('Aviso', response.data.message);
      } else {
        const message = `${response.data.message}\n\n` +
          `💰 Ganhos: R$ ${response.data.earnings.toFixed(2)}\n` +
          `⭐ XP: +${response.data.xp_gained}\n` +
          `📅 Dias trabalhados: ${response.data.days_worked}` +
          (response.data.promotion ? `\n\n🎉 ${response.data.promotion}` : '');

        Alert.alert('Ganhos Coletados!', message);
      }
      
      await loadData();
      await refreshUser();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao coletar ganhos');
    } finally {
      setWorking(false);
    }
  };

  const handleResign = () => {
    Alert.alert(
      'Pedir Demissão?',
      'Tem certeza que deseja sair deste emprego?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Sim, Sair', style: 'destructive', onPress: confirmResign },
      ]
    );
  };

  const confirmResign = async () => {
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/jobs/resign`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert('Demissão', response.data.message);
      await loadData();
      await refreshUser();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao pedir demissão');
    }
  };

  const handleWatchAd = async () => {
    setWatchingAd(true);
    setAdProgress(0);

    // Simulate ad watching (30 seconds)
    const duration = 30000; // 30 seconds
    const interval = 100; // Update every 100ms
    const steps = duration / interval;
    let currentStep = 0;

    const progressInterval = setInterval(() => {
      currentStep++;
      setAdProgress((currentStep / steps) * 100);

      if (currentStep >= steps) {
        clearInterval(progressInterval);
        completeAdWatch();
      }
    }, interval);
  };

  const completeAdWatch = async () => {
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/ads/watch`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert(
        '🎉 Boost Ativado!',
        `${response.data.message}\n\n` +
        `📈 Multiplicador: ${response.data.multiplier}x\n` +
        `💰 Ganho diário: R$ ${response.data.daily_earnings_boosted.toFixed(2)}\n` +
        `⏱️ Duração: ${response.data.seconds_remaining}s`
      );

      await loadData();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao assistir propaganda');
    } finally {
      setWatchingAd(false);
      setAdProgress(0);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEducationLabel = (level: number) => {
    const labels = ['Nenhum', 'Ensino Médio', 'Graduação', 'Mestrado', 'Doutorado'];
    return labels[level] || 'Nenhum';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.loadingText}>Carregando vagas...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Empregos</Text>
        <Ionicons name="briefcase" size={32} color="#4CAF50" />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* Current Job Section */}
        {currentJob && (
          <View style={styles.currentJobCard}>
            <View style={styles.currentJobHeader}>
              <Ionicons name="briefcase" size={24} color="#4CAF50" />
              <Text style={styles.currentJobTitle}>Emprego Atual</Text>
            </View>
            
            {/* Ad Boost Badge */}
            {adBoost.active && adBoost.multiplier > 1 && (
              <View style={styles.boostBadge}>
                <Ionicons name="flash" size={20} color="#FFD700" />
                <Text style={styles.boostText}>{adBoost.multiplier}x BOOST</Text>
                <Text style={styles.boostTimer}>{formatTime(adBoost.seconds_remaining)}</Text>
              </View>
            )}
            
            <Text style={styles.currentJobPosition}>{currentJob.position}</Text>
            <Text style={styles.currentJobCompany}>{currentJob.company}</Text>
            
            <View style={styles.salaryContainer}>
              <View>
                <Text style={styles.currentJobSalary}>
                  R$ {currentJob.salary.toLocaleString('pt-BR')}/mês
                </Text>
                <Text style={styles.dailyEarnings}>
                  R$ {((currentJob.salary / 30) * (adBoost.multiplier || 1)).toFixed(2)}/dia
                  {adBoost.multiplier > 1 && (
                    <Text style={styles.boosted}> (BOOSTED!)</Text>
                  )}
                </Text>
              </View>
            </View>
            
            <Text style={styles.currentJobDays}>
              📅 {currentJob.days_worked} dias trabalhados
            </Text>

            <View style={styles.currentJobActions}>
              {/* Watch Ad Button */}
              {!watchingAd && (
                <TouchableOpacity
                  style={styles.adButton}
                  onPress={handleWatchAd}
                >
                  <Ionicons name="play-circle" size={20} color="#fff" />
                  <Text style={styles.adButtonText}>
                    Assistir Propaganda ({adBoost.multiplier >= 10 ? 'MAX' : `+${adBoost.multiplier > 1 ? 1 : 1}x`})
                  </Text>
                </TouchableOpacity>
              )}

              {/* Ad Watching Progress */}
              {watchingAd && (
                <View style={styles.adWatchingContainer}>
                  <Text style={styles.adWatchingText}>Assistindo propaganda...</Text>
                  <View style={styles.progressBarContainer}>
                    <View style={[styles.progressBarFill, { width: `${adProgress}%` }]} />
                  </View>
                  <Text style={styles.progressText}>{Math.round(adProgress)}%</Text>
                </View>
              )}

              {/* Collect Earnings Button */}
              <TouchableOpacity
                style={[styles.workButton, working && styles.workButtonDisabled]}
                onPress={handleCollectEarnings}
                disabled={working || watchingAd}
              >
                <Ionicons name="cash" size={20} color="#fff" />
                <Text style={styles.workButtonText}>
                  {working ? 'Coletando...' : 'Coletar Ganhos'}
                </Text>
              </TouchableOpacity>

              <View style={styles.infoCard}>
                <Ionicons name="information-circle" size={16} color="#2196F3" />
                <Text style={styles.infoText}>
                  Assista propagandas para multiplicar seus ganhos até 10x! Seus ganhos acumulam automaticamente.
                </Text>
              </View>

              <TouchableOpacity style={styles.resignButton} onPress={handleResign}>
                <Text style={styles.resignButtonText}>Pedir Demissão</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Available Jobs */}
        {!currentJob && (
          <>
            <Text style={styles.sectionTitle}>
              Vagas Disponíveis ({jobs.length})
            </Text>

            {jobs.map(job => (
              <View key={job.id} style={styles.jobCard}>
                <View style={styles.jobHeader}>
                  <View style={styles.jobTitleContainer}>
                    <Text style={styles.jobTitle}>{job.title}</Text>
                    <Text style={styles.jobCompany}>{job.company}</Text>
                  </View>
                  <Text style={styles.jobSalary}>
                    R$ {job.salary.toLocaleString('pt-BR')}
                  </Text>
                </View>

                <Text style={styles.jobDescription}>{job.description}</Text>

                <View style={styles.jobInfo}>
                  <View style={styles.jobInfoItem}>
                    <Ionicons name="location" size={14} color="#888" />
                    <Text style={styles.jobInfoText}>{job.location}</Text>
                  </View>
                  <View style={styles.jobInfoItem}>
                    <Ionicons name="school" size={14} color="#888" />
                    <Text style={styles.jobInfoText}>
                      {getEducationLabel(job.requirements.education_level)}
                    </Text>
                  </View>
                  {job.requirements.experience_months > 0 && (
                    <View style={styles.jobInfoItem}>
                      <Ionicons name="time" size={14} color="#888" />
                      <Text style={styles.jobInfoText}>
                        {job.requirements.experience_months} meses exp.
                      </Text>
                    </View>
                  )}
                </View>

                {Object.keys(job.requirements.skills).length > 0 && (
                  <View style={styles.skillsRequired}>
                    <Text style={styles.skillsLabel}>Habilidades:</Text>
                    <View style={styles.skillsList}>
                      {Object.entries(job.requirements.skills).map(([skill, level]) => (
                        <View key={skill} style={styles.skillTag}>
                          <Text style={styles.skillTagText}>
                            {skill.charAt(0).toUpperCase() + skill.slice(1)} {level}/10
                          </Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )}

                <TouchableOpacity
                  style={styles.applyButton}
                  onPress={() => handleApply(job.id)}
                >
                  <Text style={styles.applyButtonText}>Candidatar-se</Text>
                  <Ionicons name="arrow-forward" size={18} color="#fff" />
                </TouchableOpacity>
              </View>
            ))}
          </>
        )}

        {currentJob && (
          <View style={styles.infoBox}>
            <Ionicons name="information-circle" size={20} color="#2196F3" />
            <Text style={styles.infoText}>
              Você já está empregado. Peça demissão para ver outras vagas.
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    padding: 16,
  },
  loadingText: {
    color: '#fff',
    textAlign: 'center',
    marginTop: 32,
  },
  currentJobCard: {
    backgroundColor: '#2a3a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  currentJobHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  currentJobTitle: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: 'bold',
    marginLeft: 8,
  },
  currentJobPosition: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  currentJobCompany: {
    fontSize: 16,
    color: '#888',
    marginBottom: 8,
  },
  currentJobSalary: {
    fontSize: 20,
    color: '#4CAF50',
    fontWeight: 'bold',
    marginBottom: 8,
  },
  currentJobDays: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 16,
  },
  currentJobActions: {
    gap: 12,
  },
  workButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  workButtonDisabled: {
    opacity: 0.6,
  },
  workButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  resignButton: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  resignButtonText: {
    color: '#F44336',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a2a3a',
    borderRadius: 8,
    padding: 12,
    gap: 8,
    marginBottom: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: '#aaa',
    lineHeight: 16,
  },
  boostBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFD700',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
    marginBottom: 12,
    gap: 6,
  },
  boostText: {
    color: '#000',
    fontSize: 14,
    fontWeight: 'bold',
  },
  boostTimer: {
    color: '#000',
    fontSize: 12,
    fontWeight: 'bold',
    backgroundColor: 'rgba(0,0,0,0.1)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  salaryContainer: {
    marginBottom: 8,
  },
  dailyEarnings: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  boosted: {
    color: '#FFD700',
    fontWeight: 'bold',
  },
  adButton: {
    backgroundColor: '#FF6B6B',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  adButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  adWatchingContainer: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  adWatchingText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  progressBarContainer: {
    width: '100%',
    height: 8,
    backgroundColor: '#3a3a3a',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#FF6B6B',
  },
  progressText: {
    color: '#888',
    fontSize: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  jobCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  jobTitleContainer: {
    flex: 1,
  },
  jobTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  jobCompany: {
    fontSize: 14,
    color: '#888',
  },
  jobSalary: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  jobDescription: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 12,
    lineHeight: 20,
  },
  jobInfo: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 12,
  },
  jobInfoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  jobInfoText: {
    fontSize: 12,
    color: '#888',
  },
  skillsRequired: {
    marginBottom: 16,
  },
  skillsLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 8,
  },
  skillsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  skillTag: {
    backgroundColor: '#3a3a3a',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  skillTagText: {
    fontSize: 12,
    color: '#aaa',
  },
  applyButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoBox: {
    backgroundColor: '#1a2a3a',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    borderWidth: 1,
    borderColor: '#2196F3',
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#aaa',
    lineHeight: 20,
  },
});
