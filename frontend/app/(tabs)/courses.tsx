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

interface Course {
  id: string;
  name: string;
  description: string;
  cost: number;
  earnings_boost: number;
  skill_boost: Record<string, number>;
  duration: string;
  level_required: number;
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
      Alert.alert(
        'Nível Insuficiente',
        `Você precisa ser nível ${course.level_required} para fazer este curso.`
      );
      return;
    }

    if ((user?.money || 0) < course.cost) {
      Alert.alert(
        'Dinheiro Insuficiente',
        `Você precisa de R$ ${course.cost.toLocaleString('pt-BR')} para fazer este curso.\n\nSeu saldo: R$ ${(user?.money || 0).toLocaleString('pt-BR')}`
      );
      return;
    }

    Alert.alert(
      `Fazer Curso: ${course.name}?`,
      `Custo: R$ ${course.cost.toLocaleString('pt-BR')}\n\nBenefícios:\n• +${(course.earnings_boost * 100).toFixed(0)}% ganhos permanentes\n• ${Object.entries(course.skill_boost).map(([skill, boost]) => `+${boost} ${skill.charAt(0).toUpperCase() + skill.slice(1)}`).join('\n• ')}\n\nEste boost é PERMANENTE!`,
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Fazer Curso', onPress: () => confirmEnroll(course) },
      ]
    );
  };

  const confirmEnroll = async (course: Course) => {
    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/courses/enroll`,
        { course_id: course.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert(
        '🎓 Curso Concluído!',
        `${response.data.message}\n\n💰 Gasto: R$ ${response.data.cost.toLocaleString('pt-BR')}\n📈 Boost: ${response.data.earnings_boost}\n\nSeus ganhos aumentaram PERMANENTEMENTE!`
      );

      await loadData();
      await refreshUser();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao fazer curso');
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

          return (
            <View key={course.id} style={[styles.courseCard, completed && styles.courseCardCompleted]}>
              <View style={styles.courseHeader}>
                <View style={styles.courseTitleContainer}>
                  <Text style={styles.courseName}>{course.name}</Text>
                  {completed && (
                    <View style={styles.completedBadge}>
                      <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                      <Text style={styles.completedText}>Concluído</Text>
                    </View>
                  )}
                </View>
                <Text style={[styles.courseCost, !canAfford && !completed && styles.courseCostExpensive]}>
                  R$ {course.cost.toLocaleString('pt-BR')}
                </Text>
              </View>

              <Text style={styles.courseDescription}>{course.description}</Text>

              <View style={styles.benefitsContainer}>
                <View style={styles.benefitItem}>
                  <Ionicons name="trending-up" size={16} color="#4CAF50" />
                  <Text style={styles.benefitText}>
                    +{(course.earnings_boost * 100).toFixed(0)}% ganhos permanentes
                  </Text>
                </View>

                {Object.entries(course.skill_boost).map(([skill, boost]) => (
                  <View key={skill} style={styles.benefitItem}>
                    <Ionicons name="star" size={16} color="#FF9800" />
                    <Text style={styles.benefitText}>
                      +{boost} {skill.charAt(0).toUpperCase() + skill.slice(1)}
                    </Text>
                  </View>
                ))}

                <View style={styles.benefitItem}>
                  <Ionicons name="time" size={16} color="#888" />
                  <Text style={styles.benefitText}>{course.duration}</Text>
                </View>

                {course.level_required > 1 && (
                  <View style={styles.benefitItem}>
                    <Ionicons name="lock-closed" size={16} color={hasLevel ? '#888' : '#F44336'} />
                    <Text style={[styles.benefitText, !hasLevel && styles.requirementNotMet]}>
                      Requer nível {course.level_required}
                    </Text>
                  </View>
                )}
              </View>

              {!completed && (
                <TouchableOpacity
                  style={[
                    styles.enrollButton,
                    (!canAfford || !hasLevel) && styles.enrollButtonDisabled,
                  ]}
                  onPress={() => handleEnroll(course)}
                >
                  <Ionicons name="school" size={20} color="#fff" />
                  <Text style={styles.enrollButtonText}>
                    {!hasLevel ? `Requer Nível ${course.level_required}` : !canAfford ? 'Dinheiro Insuficiente' : 'Fazer Curso'}
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
    padding: 20,
    marginBottom: 16,
  },
  courseCardCompleted: {
    opacity: 0.7,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  courseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  courseTitleContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  courseName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  completedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a4a2a',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  completedText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  courseCost: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  courseCostExpensive: {
    color: '#F44336',
  },
  courseDescription: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 16,
    lineHeight: 20,
  },
  benefitsContainer: {
    gap: 8,
    marginBottom: 16,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  benefitText: {
    fontSize: 14,
    color: '#aaa',
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
