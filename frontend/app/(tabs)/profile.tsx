import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  TextInput,
  Alert,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function Profile() {
  const { user, token, logout, refreshUser } = useAuth();
  const router = useRouter();
  const [showEducationModal, setShowEducationModal] = useState(false);
  const [showCertModal, setShowCertModal] = useState(false);
  const [showPhotoModal, setShowPhotoModal] = useState(false);
  const [newPhoto, setNewPhoto] = useState<string | null>(null);

  // Education form
  const [eduDegree, setEduDegree] = useState('');
  const [eduField, setEduField] = useState('');
  const [eduInstitution, setEduInstitution] = useState('');
  const [eduYear, setEduYear] = useState('');
  const [eduLevel, setEduLevel] = useState('2');

  // Certification form
  const [certName, setCertName] = useState('');
  const [certIssuer, setCertIssuer] = useState('');
  const [certBoost, setCertBoost] = useState('5');

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  const handleChangePhoto = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permissão Necessária', 'Precisamos de permissão para acessar sua galeria');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.5,
      base64: true,
    });

    if (!result.canceled && result.assets[0].base64) {
      const base64Photo = `data:image/jpeg;base64,${result.assets[0].base64}`;
      setNewPhoto(base64Photo);
      setShowPhotoModal(true);
    }
  };

  const handleSavePhoto = async () => {
    if (!newPhoto) return;

    try {
      await axios.put(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/avatar-photo`,
        { avatar_photo: newPhoto },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert('Sucesso!', 'Foto atualizada com sucesso!');
      await refreshUser();
      setShowPhotoModal(false);
      setNewPhoto(null);
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao atualizar foto');
    }
  };

  const handleDeleteEducation = (eduId: string) => {
    Alert.alert(
      'Deletar Educação?',
      'Tem certeza que deseja remover esta educação do seu perfil?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Deletar', style: 'destructive', onPress: () => confirmDeleteEducation(eduId) },
      ]
    );
  };

  const confirmDeleteEducation = async (eduId: string) => {
    try {
      await axios.delete(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/education/${eduId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert('Sucesso!', 'Educação removida com sucesso!');
      await refreshUser();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao remover educação');
    }
  };

  const handleDeleteCertification = (certId: string) => {
    Alert.alert(
      'Deletar Certificação?',
      'Tem certeza que deseja remover esta certificação do seu perfil?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Deletar', style: 'destructive', onPress: () => confirmDeleteCertification(certId) },
      ]
    );
  };

  const confirmDeleteCertification = async (certId: string) => {
    try {
      await axios.delete(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/certification/${certId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      Alert.alert('Sucesso!', 'Certificação removida com sucesso!');
      await refreshUser();
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao remover certificação');
    }
  };

  const handleAddEducation = async () => {
    if (!eduDegree || !eduField || !eduInstitution || !eduYear) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos');
      return;
    }

    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/education`,
        {
          degree: eduDegree,
          field: eduField,
          institution: eduInstitution,
          year_completed: parseInt(eduYear),
          level: parseInt(eduLevel),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      Alert.alert(
        'Sucesso!',
        `Educação adicionada! +${response.data.exp_gained} XP\nNível: ${response.data.new_level}`
      );
      
      await refreshUser();
      setShowEducationModal(false);
      setEduDegree('');
      setEduField('');
      setEduInstitution('');
      setEduYear('');
      setEduLevel('2');
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao adicionar educação');
    }
  };

  const handleAddCertification = async () => {
    if (!certName || !certIssuer) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos');
      return;
    }

    try {
      const response = await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/certification`,
        {
          name: certName,
          issuer: certIssuer,
          skill_boost: parseInt(certBoost),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      Alert.alert(
        'Sucesso!',
        `Certificação adicionada! +${response.data.exp_gained} XP\nNível: ${response.data.new_level}`
      );
      
      await refreshUser();
      setShowCertModal(false);
      setCertName('');
      setCertIssuer('');
      setCertBoost('5');
    } catch (error: any) {
      Alert.alert('Erro', error.response?.data?.detail || 'Erro ao adicionar certificação');
    }
  };

  if (!user) {
    return null;
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.avatarContainer}>
            <Ionicons name="person-circle" size={80} color="#4CAF50" />
          </View>
          <Text style={styles.name}>{user.name}</Text>
          <Text style={styles.email}>{user.email}</Text>
          <View style={styles.levelBadge}>
            <Text style={styles.levelText}>Nível {user.level}</Text>
          </View>
        </View>

        {/* Education Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Educação</Text>
            <TouchableOpacity onPress={() => setShowEducationModal(true)}>
              <Ionicons name="add-circle" size={28} color="#4CAF50" />
            </TouchableOpacity>
          </View>
          {user.education && user.education.length > 0 ? (
            user.education.map((edu: any) => (
              <View key={edu.id} style={styles.card}>
                <Ionicons name="school" size={24} color="#2196F3" />
                <View style={styles.cardContent}>
                  <Text style={styles.cardTitle}>{edu.degree}</Text>
                  <Text style={styles.cardSubtitle}>{edu.field}</Text>
                  <Text style={styles.cardInfo}>
                    {edu.institution} • {edu.year_completed}
                  </Text>
                </View>
              </View>
            ))
          ) : (
            <Text style={styles.emptyText}>Nenhuma educação adicionada ainda</Text>
          )}
        </View>

        {/* Certifications Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Certificações</Text>
            <TouchableOpacity onPress={() => setShowCertModal(true)}>
              <Ionicons name="add-circle" size={28} color="#4CAF50" />
            </TouchableOpacity>
          </View>
          {user.certifications && user.certifications.length > 0 ? (
            user.certifications.map((cert: any) => (
              <View key={cert.id} style={styles.card}>
                <Ionicons name="ribbon" size={24} color="#FF9800" />
                <View style={styles.cardContent}>
                  <Text style={styles.cardTitle}>{cert.name}</Text>
                  <Text style={styles.cardSubtitle}>{cert.issuer}</Text>
                  <Text style={styles.cardInfo}>Boost: +{cert.skill_boost}</Text>
                </View>
              </View>
            ))
          ) : (
            <Text style={styles.emptyText}>Nenhuma certificação adicionada ainda</Text>
          )}
        </View>

        {/* Work Experience Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Experiência de Trabalho</Text>
          </View>
          {user.work_experience && user.work_experience.length > 0 ? (
            user.work_experience.map((exp: any) => (
              <View key={exp.id} style={styles.card}>
                <Ionicons name="briefcase" size={24} color="#9C27B0" />
                <View style={styles.cardContent}>
                  <Text style={styles.cardTitle}>{exp.position}</Text>
                  <Text style={styles.cardSubtitle}>{exp.company}</Text>
                  <Text style={styles.cardInfo}>
                    R$ {exp.salary.toLocaleString('pt-BR')}
                  </Text>
                </View>
              </View>
            ))
          ) : (
            <Text style={styles.emptyText}>Nenhuma experiência de trabalho ainda</Text>
          )}
        </View>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out" size={24} color="#F44336" />
          <Text style={styles.logoutText}>Sair</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Education Modal */}
      <Modal
        visible={showEducationModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowEducationModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Adicionar Educação</Text>
              <TouchableOpacity onPress={() => setShowEducationModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView>
              <Text style={styles.label}>Grau</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Graduação em..."
                placeholderTextColor="#888"
                value={eduDegree}
                onChangeText={setEduDegree}
              />

              <Text style={styles.label}>Área/Campo</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Administração, Tecnologia..."
                placeholderTextColor="#888"
                value={eduField}
                onChangeText={setEduField}
              />

              <Text style={styles.label}>Instituição</Text>
              <TextInput
                style={styles.input}
                placeholder="Nome da universidade/escola"
                placeholderTextColor="#888"
                value={eduInstitution}
                onChangeText={setEduInstitution}
              />

              <Text style={styles.label}>Ano de Conclusão</Text>
              <TextInput
                style={styles.input}
                placeholder="2024"
                placeholderTextColor="#888"
                value={eduYear}
                onChangeText={setEduYear}
                keyboardType="number-pad"
              />

              <Text style={styles.label}>Nível (1=Médio, 2=Graduação, 3=Mestrado, 4=Doutorado)</Text>
              <TextInput
                style={styles.input}
                placeholder="2"
                placeholderTextColor="#888"
                value={eduLevel}
                onChangeText={setEduLevel}
                keyboardType="number-pad"
              />

              <TouchableOpacity style={styles.submitButton} onPress={handleAddEducation}>
                <Text style={styles.submitButtonText}>Adicionar</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Certification Modal */}
      <Modal
        visible={showCertModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCertModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Adicionar Certificação</Text>
              <TouchableOpacity onPress={() => setShowCertModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView>
              <Text style={styles.label}>Nome da Certificação</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: PMP, AWS Certified..."
                placeholderTextColor="#888"
                value={certName}
                onChangeText={setCertName}
              />

              <Text style={styles.label}>Emissor</Text>
              <TextInput
                style={styles.input}
                placeholder="Organização que emitiu"
                placeholderTextColor="#888"
                value={certIssuer}
                onChangeText={setCertIssuer}
              />

              <Text style={styles.label}>Boost de Habilidade (1-10)</Text>
              <TextInput
                style={styles.input}
                placeholder="5"
                placeholderTextColor="#888"
                value={certBoost}
                onChangeText={setCertBoost}
                keyboardType="number-pad"
              />

              <TouchableOpacity style={styles.submitButton} onPress={handleAddCertification}>
                <Text style={styles.submitButtonText}>Adicionar</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
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
  header: {
    alignItems: 'center',
    paddingVertical: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
    marginBottom: 24,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  email: {
    fontSize: 16,
    color: '#888',
    marginBottom: 12,
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
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  card: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    marginBottom: 12,
  },
  cardContent: {
    marginLeft: 12,
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#888',
    marginBottom: 4,
  },
  cardInfo: {
    fontSize: 12,
    color: '#666',
  },
  emptyText: {
    color: '#666',
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: 24,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginTop: 24,
  },
  logoutText: {
    color: '#F44336',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  label: {
    fontSize: 14,
    color: '#888',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
  },
  submitButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 16,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
