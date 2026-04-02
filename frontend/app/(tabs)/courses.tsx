import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Course {
  id: string;
  name: string;
  description: string;
  cost: number;
  earnings_boost: number;
  skill_boost: Record<string, number>;
  duration: string;
  level_required: number;
  institution?: string;
  category?: string;
  icon?: string;
}

interface MyCourse {
  id: string;
  course_id: string;
  course_name: string;
  earnings_boost: number;
  completed_at: string;
}

export default function Courses() {
  const { user, token, refreshUser } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [myCourses, setMyCourses] = useState<MyCourse[]>([]);
  const [totalBoost, setTotalBoost] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [coursesRes, myCoursesRes] = await Promise.all([
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/courses`),
        axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/courses/my-courses`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setCourses(coursesRes.data);
      setMyCourses(myCoursesRes.data.courses || []);
      setTotalBoost(myCoursesRes.data.total_boost || 0);
    } catch (error) {
      console.error('Error loading courses:', error);
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

  const handleEnroll = (course: Course) => {
    if ((user?.level || 1) < course.level_required) {
      if (Platform.OS === 'web') {
        window.alert(`Nível Insuficiente\n\nVocê precisa ser nível ${course.level_required} para fazer este curso.`);
      } else {
        Alert.alert(
          'Nível Insuficiente',
          `Você precisa ser nível ${course.level_required} para fazer este curso.`
        );
      }
      return;
    }

    if ((user?.money || 0) < course.cost) {
      if (Platform.OS === 'web') {
        window.alert(`Dinheiro Insuficiente\n\nVocê precisa de R$ ${course.cost.toLocaleString('pt-BR')} para fazer este curso.\nSeu saldo: R$ ${(user?.money || 0).toLocaleString('pt-BR')}`);
      } else {
        Alert.alert(
          'Dinheiro Insuficiente',
          `Você precisa de R$ ${course.cost.toLocaleString('pt-BR')} para fazer este curso.\n\nSeu saldo: R$ ${(user?.money || 0).toLocaleString('pt-BR')}`
        );
      }
      return;
    }

    const courseInfo = `Custo: R$ ${course.cost.toLocaleString('pt-BR')}\nBenefícios: +${(course.earnings_boost * 100).toFixed(0)}% ganhos permanentes`;

    if (Platform.OS === 'web') {
      const ok = window.confirm(`Fazer Curso: ${course.name}?\n\n${courseInfo}\n\nEste boost é PERMANENTE!`);
      if (ok) confirmEnroll(course);
    } else {
      Alert.alert(
        `Fazer Curso: ${course.name}?`,
        `${courseInfo}\n\n${Object.entries(course.skill_boost).map(([skill, boost]) => `+${boost} ${skill.charAt(0).toUpperCase() + skill.slice(1)}`).join('\n')}\n\nEste boost é PERMANENTE!`,
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Fazer Curso', onPress: () => confirmEnroll(course) },
        ]
      );
    }
  };

  const confirmEnroll = async (course: Course) => {
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/courses/enroll`,
        { course_id: course.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const successMsg = `${response.data.message}\n\nGasto: R$ ${response.data.cost.toLocaleString('pt-BR')}\nBoost: ${response.data.earnings_boost}\n\nSeus ganhos aumentaram PERMANENTEMENTE!`;
      if (Platform.OS === 'web') {
        window.alert(`Curso Concluído!\n\n${successMsg}`);
      } else {
        Alert.alert('Curso Concluído!', successMsg);
      }

      await loadData();
      await refreshUser();
    } catch (error: any) {
      const errMsg = error.response?.data?.detail || 'Erro ao fazer curso';
      if (Platform.OS === 'web') {
        window.alert(`Erro\n\n${errMsg}`);
      } else {
        Alert.alert('Erro', errMsg);
      }
    }
  };

  const isCompleted = (courseId: string) => {
    return myCourses.some(c => c.course_id === courseId);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.loadingText}>Carregando cursos...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Cursos</Text>
          <Text style={styles.subtitle}>Aumente seus ganhos permanentemente</Text>
        </View>
        <Ionicons name="school" size={32} color="#4CAF50" />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* My Courses Summary */}
        {myCourses.length > 0 && (
          <View style={styles.summaryCard}>
            <View style={styles.summaryHeader}>
              <Ionicons name="trophy" size={24} color="#FFD700" />
              <Text style={styles.summaryTitle}>Seus Cursos</Text>
            </View>
            <Text style={styles.summaryCount}>{myCourses.length} curso(s) completado(s)</Text>
            <Text style={styles.summaryBoost}>
              Boost Total: +{(totalBoost * 100).toFixed(0)}% ganhos permanentes 🚀
            </Text>
          </View>
        )}

        {/* Available Courses */}
        <Text style={styles.sectionTitle}>Cursos Disponíveis</Text>

        {courses.map(course => {
          const completed = isCompleted(course.id);
          const canAfford = (user?.money || 0) >= course.cost;
          const hasLevel = (user?.level || 1) >= course.level_required;
          const isLocked = !hasLevel;

          return (
            <View key={course.id} style={[styles.courseCard, completed && styles.courseCardCompleted, isLocked && styles.courseCardLocked]}>
              {isLocked && (
                <View style={styles.lockedOverlay}>
                  <Ionicons name="lock-closed" size={20} color="#F44336" />
                  <Text style={styles.lockedText}>Nível {course.level_required}</Text>
                </View>
              )}
              <View style={styles.courseHeader}>
                <View style={styles.courseTitleContainer}>
                  <View style={[styles.courseIconBg, { backgroundColor: isLocked ? '#3a3a3a' : '#4CAF5020' }]}>
                    <Ionicons name={(course.icon || 'school') as any} size={20} color={isLocked ? '#666' : '#4CAF50'} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.courseName, isLocked && { color: '#666' }]}>{course.name}</Text>
                    {course.institution && (
                      <Text style={styles.courseInstitution}>{course.institution}</Text>
                    )}
                  </View>
                  {completed && (
                    <View style={styles.completedBadge}>
                      <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                    </View>
                  )}
                </View>
              </View>

              <Text style={[styles.courseDescription, isLocked && { color: '#555' }]}>{course.description}</Text>

              <View style={styles.benefitsContainer}>
                <View style={styles.benefitRow}>
                  <View style={styles.benefitItem}>
                    <Ionicons name="trending-up" size={14} color={isLocked ? '#555' : '#4CAF50'} />
                    <Text style={[styles.benefitText, isLocked && { color: '#555' }]}>
                      +{(course.earnings_boost * 100).toFixed(0)}% ganhos
                    </Text>
                  </View>
                  <View style={styles.benefitItem}>
                    <Ionicons name="cash" size={14} color={!canAfford && !completed && !isLocked ? '#F44336' : isLocked ? '#555' : '#FFD700'} />
                    <Text style={[styles.benefitText, !canAfford && !completed && !isLocked && { color: '#F44336' }, isLocked && { color: '#555' }]}>
                      R$ {course.cost.toLocaleString('pt-BR')}
                    </Text>
                  </View>
                </View>

                <View style={styles.skillChips}>
                  {Object.entries(course.skill_boost).map(([skill, boost]) => (
                    <View key={skill} style={[styles.skillChip, isLocked && { backgroundColor: '#2a2a2a' }]}>
                      <Text style={[styles.skillChipText, isLocked && { color: '#555' }]}>
                        +{boost} {skill.charAt(0).toUpperCase() + skill.slice(1)}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>

              {!completed && !isLocked && (
                <TouchableOpacity
                  style={[
                    styles.enrollButton,
                    !canAfford && styles.enrollButtonDisabled,
                  ]}
                  onPress={() => handleEnroll(course)}
                >
                  <Ionicons name="school" size={18} color="#fff" />
                  <Text style={styles.enrollButtonText}>
                    {!canAfford ? 'Dinheiro Insuficiente' : 'Fazer Curso'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          );
        })}

        {/* Info Box */}
        <View style={styles.infoBox}>
          <Ionicons name="information-circle" size={20} color="#2196F3" />
          <Text style={styles.infoText}>
            Os cursos aumentam seus ganhos PERMANENTEMENTE! Investir em educação sempre vale a pena. 📚
          </Text>
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
  subtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  content: {
    padding: 16,
  },
  loadingText: {
    color: '#fff',
    textAlign: 'center',
    marginTop: 32,
  },
  summaryCard: {
    backgroundColor: '#2a3a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginLeft: 8,
  },
  summaryCount: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 8,
  },
  summaryBoost: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  courseCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  courseCardCompleted: {
    opacity: 0.7,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  courseCardLocked: {
    opacity: 0.6,
    borderWidth: 1,
    borderColor: '#333',
  },
  lockedOverlay: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F4433620',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 10,
  },
  lockedText: {
    color: '#F44336',
    fontSize: 12,
    fontWeight: 'bold',
  },
  courseHeader: {
    marginBottom: 8,
  },
  courseTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  courseIconBg: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  courseName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  courseInstitution: {
    fontSize: 11,
    color: '#888',
    marginTop: 2,
  },
  completedBadge: {
    backgroundColor: '#2a4a2a',
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  completedText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  courseDescription: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 16,
    lineHeight: 20,
  },
  benefitsContainer: {
    gap: 8,
    marginBottom: 12,
  },
  benefitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  benefitText: {
    fontSize: 13,
    color: '#aaa',
  },
  skillChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 4,
  },
  skillChip: {
    backgroundColor: '#FF980015',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  skillChipText: {
    color: '#FF9800',
    fontSize: 12,
    fontWeight: '600',
  },
  requirementNotMet: {
    color: '#F44336',
  },
  enrollButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  enrollButtonDisabled: {
    backgroundColor: '#3a3a3a',
  },
  enrollButtonText: {
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
    marginTop: 8,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#aaa',
    lineHeight: 20,
  },
});
