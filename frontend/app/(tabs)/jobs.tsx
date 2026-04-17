import { safeFixed } from '../../utils/safeFixed';
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
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
  const { colors } = useTheme();
import { useLanguage } from '../../context/LanguageContext';
import { useRouter } from 'expo-router';
import { SkeletonList } from '../../components/SkeletonLoader';
import { useHaptics } from '../../hooks/useHaptics';
import { useSound } from '../../context/SoundContext';
import { useTheme } from '../../context/ThemeContext';

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

interface JobApplication {
  id: string;
  user_id: string;
  job_id: string;
  status: string;
  match_score: number;
  job?: Job;
}

interface CurrentJob {
  company: string;
  position: string;
  salary: number;
  days_worked: number;
  last_collection_date: string | null;
  job_id?: string;
}

interface AdBoost {
  active: boolean;
  multiplier: number;
  ads_watched: number;
  seconds_remaining: number;
}

export default function Jobs() {
  const { token, refreshUser } = useAuth();
  const { trigger: haptic } = useHaptics();
  const { playClick, playSuccess } = useSound();
  const { t, formatMoney } = useLanguage();
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [currentJob, setCurrentJob] = useState<CurrentJob | null>(null);
  const [adBoost, setAdBoost] = useState<AdBoost>({ active: false, multiplier: 1, ads_watched: 0, seconds_remaining: 0 });
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [watchingAd, setWatchingAd] = useState(false);
  const [adProgress, setAdProgress] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  // Boost timer
  useEffect(() => {
    if (!adBoost.active || adBoost.seconds_remaining <= 0) return;
    const interval = setInterval(() => {
      setAdBoost(prev => {
        if (prev.seconds_remaining <= 1) {
          return { ...prev, seconds_remaining: 0, active: false, multiplier: 1 };
        }
        return { ...prev, seconds_remaining: prev.seconds_remaining - 1 };
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [adBoost.active]);

  const loadData = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [jobsRes, currentJobRes, boostRes, appsRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/jobs/available-for-level`, { headers }),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/jobs/current`, { headers }).catch(() => ({ data: null })),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/ads/current-boost`, { headers }).catch(() => ({ data: { active: false, multiplier: 1, ads_watched: 0, seconds_remaining: 0 } })),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/jobs/my-applications`, { headers }).catch(() => ({ data: [] })),
      ]);

      setJobs(jobsRes.data);
      setCurrentJob(currentJobRes.data);
      setAdBoost(boostRes.data);
      setApplications(appsRes.data || []);
    } catch (error) {
      console.error('Error loading jobs:', error);
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

  const getApplicationForJob = (jobId: string): JobApplication | undefined => {
    return applications.find(a => a.job_id === jobId);
  };

  const handleApply = async (jobId: string) => {
    setApplying(jobId);
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/jobs/apply`,
        { job_id: jobId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.status === 'accepted') {
        if (Platform.OS === 'web') {
          const ok = window.confirm(`Aprovado!\n\n${response.data.message}\nCompatibilidade: ${safeFixed(response.data.match_score, 0)}%\n\nDeseja aceitar a vaga?`);
          if (ok) handleAccept(jobId);
        } else {
          Alert.alert(
            'Aprovado!',
            `${response.data.message}\n\nCompatibilidade: ${safeFixed(response.data.match_score, 0)}%`,
            [
              { text: 'Ver Depois', style: 'cancel' },
              { text: 'Aceitar Vaga', onPress: () => handleAccept(jobId) },
            ]
          );
        }
      } else {
        if (Platform.OS === 'web') {
          window.alert(`Candidatura Enviada\n\n${response.data.message}\nCompatibilidade: ${safeFixed(response.data.match_score, 0)}%`);
        } else {
          Alert.alert(
            'Candidatura Enviada',
            `${response.data.message}\n\nCompatibilidade: ${safeFixed(response.data.match_score, 0)}%\n\nSua candidatura foi registrada mas o match precisa ser maior para aprovação automática.`
          );
        }
      }

      await loadData();
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Erro ao candidatar-se';
      Alert.alert(t('general.error'), detail);
    } finally {
      setApplying(null);
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
        'Parabéns!',
        `${response.data.message}\n\nGanho diário: $ ${safeFixed(response.data.daily_earnings, 2)}`
      );
      await loadData();
      await refreshUser();
    } catch (error: any) {
      Alert.alert(t('general.error'), error.response?.data?.detail || 'Erro ao aceitar vaga');
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
        let message = `${response.data.message}\n\n` +
          `Ganhos: $ ${safeFixed(response.data.earnings, 2)}\n` +
          `XP: +${response.data.xp_gained}\n` +
          `Dias trabalhados: ${response.data.days_worked}`;
        
        if (response.data.boost_multiplier > 1) {
          message += `\nBoost Propaganda: ${response.data.boost_multiplier}x`;
        }
        if (response.data.courses_boost > 0) {
          message += `\nBoost Cursos: +${safeFixed((response.data.courses_boost || 0) * 100, 0)}%`;
        }
        if (response.data.promotion) {
          message += `\n\n${response.data.promotion}`;
        }

        Alert.alert('Ganhos Coletados!', message);
      }

      await loadData();
      await refreshUser();
    } catch (error: any) {
      Alert.alert(t('general.error'), error.response?.data?.detail || 'Erro ao coletar ganhos');
    } finally {
      setWorking(false);
    }
  };

  const handleResign = () => {
    if (Platform.OS === 'web') {
      const ok = window.confirm('Pedir Demissão?\n\nTem certeza que deseja sair deste emprego? Você poderá se candidatar a novas vagas.');
      if (ok) confirmResign();
    } else {
      Alert.alert(
        'Pedir Demissão?',
        'Tem certeza que deseja sair deste emprego? Você poderá se candidatar a novas vagas.',
        [
          { text: t('general.cancel'), style: 'cancel' },
          { text: 'Sim, Sair', style: 'destructive', onPress: confirmResign },
        ]
      );
    }
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
      Alert.alert(t('general.error'), error.response?.data?.detail || 'Erro ao pedir demissão');
    }
  };

  const handleWatchAd = async () => {
    setWatchingAd(true);
    setAdProgress(0);

    const duration = 30000;
    const interval = 100;
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

      const secs = response.data.seconds_remaining;
      const hrs = Math.floor(secs / 3600);
      const mins = Math.floor((secs % 3600) / 60);
      const durStr = hrs > 0 ? `${hrs}h${mins.toString().padStart(2, '0')}m` : `${mins} min`;

      const title = 'Boost Ativado!';
      const msg = `${response.data.message}\n\n` +
        `Multiplicador: ${response.data.multiplier}x\n` +
        `Ganho diário: $ ${safeFixed(response.data.daily_earnings_boosted, 2)}\n` +
        `Duração restante: ${durStr}`;

      if (Platform.OS === 'web') {
        window.alert(`${title}\n\n${msg}`);
      } else {
        Alert.alert(title, msg);
      }

      await loadData();
    } catch (error: any) {
      Alert.alert(t('general.error'), error.response?.data?.detail || 'Erro ao assistir propaganda');
    } finally {
      setWatchingAd(false);
      setAdProgress(0);
    }
  };

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hrs > 0) return `${hrs}h${mins.toString().padStart(2, '0')}m`;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEducationLabel = (level: number) => {
    const labels: Record<number, string> = { 0: 'Nenhum', 1: 'Ensino Médio', 2: 'Graduação', 3: 'Mestrado', 4: 'Doutorado' };
    return labels[level] || 'Nenhum';
  };

  // Filter out accepted applications for display
  const acceptedApps = applications.filter(a => a.status === 'accepted');

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <SkeletonList count={4} style={{ padding: 16 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{t('jobs.title')}</Text>
        <Ionicons name="briefcase" size={32} color="#4CAF50" />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* Courses Banner */}
        <TouchableOpacity
          style={{ flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: colors.card, borderRadius: 14, padding: 14, marginBottom: 16, borderWidth: 1, borderColor: '#4CAF5040' }}
          onPress={() => router.push('/(tabs)/courses')}
          activeOpacity={0.7}
        >
          <View style={{ width: 42, height: 42, borderRadius: 12, backgroundColor: '#4CAF5025', justifyContent: 'center', alignItems: 'center' }}>
            <Ionicons name="school" size={22} color="#4CAF50" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ color: colors.text, fontSize: 15, fontWeight: 'bold' }}>Cursos Harvard & MIT</Text>
            <Text style={{ color: colors.textMuted, fontSize: 12, marginTop: 2 }}>Aumente suas habilidades e desbloqueie vagas melhores</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#4CAF50" />
        </TouchableOpacity>

        {/* ===== CURRENT JOB SECTION ===== */}
        {currentJob && (
          <View style={styles.currentJobCard}>
            <View style={styles.currentJobHeader}>
              <Ionicons name="briefcase" size={24} color="#4CAF50" />
              <Text style={styles.currentJobLabel}>{t('jobs.current')}</Text>
            </View>

            {/* Ad Boost Badge */}
            {adBoost.active && adBoost.multiplier > 1 && (
              <View style={styles.boostBadge}>
                <Ionicons name="flash" size={18} color="#000" />
                <Text style={styles.boostText}>{adBoost.multiplier}x BOOST</Text>
                <Text style={styles.boostTimer}>{formatTime(adBoost.seconds_remaining)}</Text>
              </View>
            )}

            <Text style={styles.currentJobPosition}>{currentJob.position}</Text>
            <Text style={styles.currentJobCompany}>{currentJob.company}</Text>

            <View style={styles.salaryRow}>
              <Text style={styles.currentJobSalary}>
                {formatMoney(currentJob.salary)}/{t('general.month')}
              </Text>
              <Text style={styles.dailyEarnings}>
                $ {safeFixed((currentJob.salary / 30) * (adBoost.active ? adBoost.multiplier : 1), 2)}/dia
                {adBoost.active && adBoost.multiplier > 1 && (
                  <Text style={styles.boosted}> BOOST!</Text>
                )}
              </Text>
            </View>

            <Text style={styles.currentJobDays}>
              {currentJob.days_worked} dias trabalhados
            </Text>

            <View style={styles.actionButtons}>
              {/* Collect Earnings */}
              <TouchableOpacity
                style={[styles.collectButton, working && styles.buttonDisabled]}
                onPress={handleCollectEarnings}
                disabled={working || watchingAd}
              >
                <Ionicons name="cash" size={20} color="#fff" />
                <Text style={styles.collectButtonText}>
                  {working ? 'Coletando...' : 'Coletar Ganhos'}
                </Text>
              </TouchableOpacity>

              {/* Watch Ad */}
              {!watchingAd ? (
                <TouchableOpacity
                  style={styles.adButton}
                  onPress={handleWatchAd}
                  disabled={adBoost.multiplier >= 10}
                >
                  <Ionicons name="play-circle" size={20} color="#fff" />
                  <Text style={styles.adButtonText}>
                    {adBoost.multiplier >= 10 ? 'Boost MAX!' : `Assistir Propaganda (+1x por 1h)`}
                  </Text>
                </TouchableOpacity>
              ) : (
                <View style={styles.adWatchingContainer}>
                  <Text style={styles.adWatchingText}>Assistindo propaganda...</Text>
                  <View style={styles.progressBarContainer}>
                    <View style={[styles.progressBarFill, { width: `${adProgress}%` }]} />
                  </View>
                  <Text style={styles.progressText}>{Math.round(adProgress)}%</Text>
                </View>
              )}

              {/* Info */}
              <View style={styles.infoCard}>
                <Ionicons name="information-circle" size={16} color="#2196F3" />
                <Text style={styles.infoCardText}>
                  Assista propagandas para multiplicar ganhos até 10x! Ganhos acumulam automaticamente.
                </Text>
              </View>

              {/* Courses Link */}
              <TouchableOpacity
                style={styles.coursesLink}
                onPress={() => router.push('/(tabs)/courses')}
              >
                <Ionicons name="school" size={20} color="#4CAF50" />
                <Text style={styles.coursesLinkText}>
                  Fazer Cursos (Boost Permanente)
                </Text>
                <Ionicons name="arrow-forward" size={20} color="#4CAF50" />
              </TouchableOpacity>

              {/* Resign */}
              <TouchableOpacity style={styles.resignButton} onPress={handleResign}>
                <Text style={styles.resignButtonText}>Pedir Demissão</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ===== ACCEPTED OFFERS (not yet started working) ===== */}
        {!currentJob && acceptedApps.length > 0 && (
          <View style={styles.sectionContainer}>
            <View style={styles.sectionHeaderRow}>
              <Ionicons name="checkmark-circle" size={22} color="#4CAF50" />
              <Text style={styles.sectionTitle}>Ofertas Aprovadas</Text>
            </View>
            {acceptedApps.map(app => (
              <View key={app.id} style={styles.acceptedCard}>
                <View style={styles.acceptedInfo}>
                  <Text style={styles.acceptedJobTitle}>{app.job?.title || 'Vaga'}</Text>
                  <Text style={styles.acceptedJobCompany}>{app.job?.company || ''}</Text>
                  <Text style={styles.acceptedMatch}>
                    Compatibilidade: {safeFixed(app.match_score, 0)}%
                  </Text>
                  {app.job?.salary && (
                    <Text style={styles.acceptedSalary}>
                      {formatMoney(app.job.salary)}/{t('general.month')}
                    </Text>
                  )}
                </View>
                <TouchableOpacity
                  style={styles.acceptButton}
                  onPress={() => handleAccept(app.job_id)}
                >
                  <Text style={styles.acceptButtonText}>Aceitar</Text>
                  <Ionicons name="checkmark" size={18} color="#fff" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* ===== AVAILABLE JOBS ===== */}
        {!currentJob && (
          <View style={styles.sectionContainer}>
            <View style={styles.sectionHeaderRow}>
              <Ionicons name="search" size={22} color="#888" />
              <Text style={styles.sectionTitle}>
                {t('jobs.available')} ({jobs.length})
              </Text>
            </View>

            {jobs.map(job => {
              const existingApp = getApplicationForJob(job.id);
              const isApplied = !!existingApp;
              const isAccepted = existingApp?.status === 'accepted';
              const isPending = existingApp?.status === 'pending';
              const isApplyingThis = applying === job.id;

              return (
                <View key={job.id} style={[styles.jobCard, isApplied && styles.jobCardApplied, job.is_premium && styles.premiumJobCard]}>
                  {job.is_premium && (
                    <View style={styles.premiumBadge}>
                      <Ionicons name="star" size={12} color="#000" />
                      <Text style={styles.premiumBadgeText}>PREMIUM Nv{job.min_level}+</Text>
                    </View>
                  )}
                  <View style={styles.jobHeader}>
                    <View style={styles.jobTitleContainer}>
                      <Text style={styles.jobTitle}>{job.title}</Text>
                      <Text style={styles.jobCompany}>{job.company}</Text>
                    </View>
                    <Text style={[styles.jobSalary, job.is_premium && { color: '#FFD700' }]}>
                      {formatMoney(job.salary)}
                    </Text>
                  </View>

                  <Text style={styles.jobDescription}>{job.description}</Text>

                  <View style={styles.jobInfoRow}>
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
                      <Text style={styles.skillsLabel}>{t('general.skills')}:</Text>
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

                  {/* Action Button */}
                  {isAccepted ? (
                    <TouchableOpacity
                      style={styles.acceptJobButton}
                      onPress={() => handleAccept(job.id)}
                    >
                      <Ionicons name="checkmark-circle" size={18} color="#fff" />
                      <Text style={styles.acceptJobButtonText}>Aceitar Vaga</Text>
                    </TouchableOpacity>
                  ) : isPending ? (
                    <View style={styles.pendingBadge}>
                      <Ionicons name="hourglass" size={18} color="#FF9800" />
                      <Text style={styles.pendingText}>Candidatura Pendente</Text>
                    </View>
                  ) : (
                    <TouchableOpacity
                      style={[styles.applyButton, isApplyingThis && styles.buttonDisabled]}
                      onPress={() => handleApply(job.id)}
                      disabled={isApplyingThis}
                    >
                      {isApplyingThis ? (
                        <ActivityIndicator size="small" color="#fff" />
                      ) : (
                        <>
                          <Text style={styles.applyButtonText}>{t('jobs.apply')}</Text>
                          <Ionicons name="arrow-forward" size={18} color="#fff" />
                        </>
                      )}
                    </TouchableOpacity>
                  )}
                </View>
              );
            })}
          </View>
        )}

        {/* Info when employed */}
        {currentJob && (
          <View style={styles.infoBox}>
            <Ionicons name="information-circle" size={20} color="#2196F3" />
            <Text style={styles.infoBoxText}>
              Você está empregado. Peça demissão para ver e candidatar-se a outras vagas.
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
    borderBottomColor: '#333',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    color: '#888',
    fontSize: 16,
  },

  // Current Job
  currentJobCard: {
    backgroundColor: '#1e1e1e',
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
    gap: 8,
  },
  currentJobLabel: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: 'bold',
    textTransform: 'uppercase',
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
    marginBottom: 12,
  },
  salaryRow: {
    marginBottom: 8,
  },
  currentJobSalary: {
    fontSize: 20,
    color: '#4CAF50',
    fontWeight: 'bold',
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
  currentJobDays: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 16,
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

  // Action Buttons
  actionButtons: {
    gap: 12,
  },
  collectButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  collectButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  adButton: {
    backgroundColor: '#FF6B6B',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
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
  infoCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#1e1e1e',
    borderRadius: 8,
    padding: 12,
    gap: 8,
  },
  infoCardText: {
    flex: 1,
    fontSize: 12,
    color: '#aaa',
    lineHeight: 16,
  },
  coursesLink: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  coursesLinkText: {
    flex: 1,
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: 'bold',
    marginHorizontal: 12,
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

  // Sections
  sectionContainer: {
    marginBottom: 20,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },

  // Accepted Offers
  acceptedCard: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  acceptedInfo: {
    flex: 1,
  },
  acceptedJobTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  acceptedJobCompany: {
    fontSize: 14,
    color: '#888',
    marginBottom: 4,
  },
  acceptedMatch: {
    fontSize: 12,
    color: '#4CAF50',
    marginBottom: 2,
  },
  acceptedSalary: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  acceptButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  acceptButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },

  // Job Cards
  jobCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  jobCardApplied: {
    borderWidth: 1,
    borderColor: '#555',
    opacity: 0.85,
  },
  premiumJobCard: {
    borderWidth: 1,
    borderColor: '#FFD700',
    backgroundColor: '#1e1e1e',
  },
  premiumBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFD700',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 10,
  },
  premiumBadgeText: {
    color: '#000',
    fontSize: 10,
    fontWeight: 'bold',
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  jobTitleContainer: {
    flex: 1,
    marginRight: 12,
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
  jobInfoRow: {
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

  // Apply Button
  applyButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    minHeight: 48,
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },

  // Accept Job (in job card)
  acceptJobButton: {
    backgroundColor: '#2196F3',
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  acceptJobButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },

  // Pending Badge
  pendingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3a3a2a',
    borderRadius: 12,
    padding: 14,
    gap: 8,
    borderWidth: 1,
    borderColor: '#FF9800',
  },
  pendingText: {
    color: '#FF9800',
    fontSize: 14,
    fontWeight: 'bold',
  },

  // Info Box
  infoBox: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
    borderWidth: 1,
    borderColor: '#2196F3',
  },
  infoBoxText: {
    flex: 1,
    fontSize: 14,
    color: '#aaa',
    lineHeight: 20,
  },
});
