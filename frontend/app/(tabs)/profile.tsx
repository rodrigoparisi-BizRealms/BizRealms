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
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import * as ImagePicker from 'expo-image-picker';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function Profile() {
  const { user, token, logout, refreshUser } = useAuth();
  const router = useRouter();
  const [showEducationModal, setShowEducationModal] = useState(false);
  const [showCertModal, setShowCertModal] = useState(false);
  const [showPhotoModal, setShowPhotoModal] = useState(false);
  const [newPhoto, setNewPhoto] = useState<string | null>(null);
  const [savingPhoto, setSavingPhoto] = useState(false);

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

  // Personal data form
  const [showPersonalModal, setShowPersonalModal] = useState(false);
  const [personalData, setPersonalData] = useState({
    full_name: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    phone: '',
  });
  const [savingPersonal, setSavingPersonal] = useState(false);

  // PIX key form
  const [showPixModal, setShowPixModal] = useState(false);
  const [pixKey, setPixKey] = useState('');
  const [pixType, setPixType] = useState('cpf');
  const [savingPix, setSavingPix] = useState(false);

  const showAlert = (title: string, msg: string) => {
    if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
    else Alert.alert(title, msg);
  };

  const openPersonalData = () => {
    setPersonalData({
      full_name: (user as any)?.full_name || user?.name || '',
      address: (user as any)?.address || '',
      city: (user as any)?.city || '',
      state: (user as any)?.state || '',
      zip_code: (user as any)?.zip_code || '',
      phone: (user as any)?.phone || '',
    });
    setShowPersonalModal(true);
  };

  const handleSavePersonalData = async () => {
    setSavingPersonal(true);
    try {
      await axios.put(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/personal-data`,
        personalData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      showAlert('Sucesso!', 'Dados pessoais atualizados com sucesso');
      await refreshUser();
      setShowPersonalModal(false);
    } catch (e: any) {
      showAlert('Erro', e.response?.data?.detail || 'Erro ao salvar dados');
    } finally { setSavingPersonal(false); }
  };

  const openPixModal = () => {
    setPixKey((user as any)?.pix_key || '');
    setPixType((user as any)?.pix_type || 'cpf');
    setShowPixModal(true);
  };

  const handleSavePix = async () => {
    if (!pixKey.trim()) { showAlert('Erro', 'Informe sua chave PIX'); return; }
    setSavingPix(true);
    try {
      await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/rewards/update-pix`,
        { pix_key: pixKey, pix_type: pixType },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      showAlert('Sucesso!', 'Chave PIX salva com sucesso!');
      await refreshUser();
      setShowPixModal(false);
    } catch (e: any) {
      showAlert('Erro', e.response?.data?.detail || 'Erro ao salvar PIX');
    } finally { setSavingPix(false); }
  };

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/login');
  };

  const handleChangePhoto = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();

      if (status !== 'granted') {
        Alert.alert('Permissão Necessária', 'Precisamos de permissão para acessar sua galeria');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
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
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Erro', 'Não foi possível selecionar a imagem');
    }
  };

  const handleSavePhoto = async () => {
    if (!newPhoto) return;
    setSavingPhoto(true);

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
    } finally {
      setSavingPhoto(false);
    }
  };

  const handleRemovePhoto = async () => {
    const doRemove = async () => {
      try {
        await axios.put(
          `${EXPO_PUBLIC_BACKEND_URL}/api/user/avatar-photo`,
          { avatar_photo: null },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (Platform.OS === 'web') window.alert('Foto removida!');
        else Alert.alert('Sucesso!', 'Foto removida');
        await refreshUser();
      } catch (error: any) {
        if (Platform.OS === 'web') window.alert('Erro ao remover foto');
        else Alert.alert('Erro', 'Erro ao remover foto');
      }
    };

    if (Platform.OS === 'web') {
      const ok = window.confirm('Remover Foto?\n\nDeseja voltar ao avatar padrão?');
      if (ok) doRemove();
    } else {
      Alert.alert(
        'Remover Foto?',
        'Deseja voltar ao avatar padrão?',
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Remover', style: 'destructive', onPress: doRemove },
        ]
      );
    }
  };

  const handleDeleteEducation = (eduId: string, eduName: string) => {
    const doDelete = async () => {
      try {
        await axios.delete(
          `${EXPO_PUBLIC_BACKEND_URL}/api/user/education/${eduId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (Platform.OS === 'web') window.alert('Educação removida!');
        else Alert.alert('Sucesso!', 'Educação removida');
        await refreshUser();
      } catch (error: any) {
        const msg = error.response?.data?.detail || 'Erro ao remover educação';
        if (Platform.OS === 'web') window.alert(`Erro: ${msg}`);
        else Alert.alert('Erro', msg);
      }
    };

    if (Platform.OS === 'web') {
      const ok = window.confirm(`Remover Educação?\n\nDeseja remover "${eduName}" do seu perfil?`);
      if (ok) doDelete();
    } else {
      Alert.alert('Remover Educação?', `Deseja remover "${eduName}" do seu perfil?`, [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Remover', style: 'destructive', onPress: doDelete },
      ]);
    }
  };

  const handleDeleteCertification = (certId: string, certNameStr: string) => {
    const doDelete = async () => {
      try {
        await axios.delete(
          `${EXPO_PUBLIC_BACKEND_URL}/api/user/certification/${certId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (Platform.OS === 'web') window.alert('Certificação removida!');
        else Alert.alert('Sucesso!', 'Certificação removida');
        await refreshUser();
      } catch (error: any) {
        const msg = error.response?.data?.detail || 'Erro ao remover certificação';
        if (Platform.OS === 'web') window.alert(`Erro: ${msg}`);
        else Alert.alert('Erro', msg);
      }
    };

    if (Platform.OS === 'web') {
      const ok = window.confirm(`Remover Certificação?\n\nDeseja remover "${certNameStr}" do seu perfil?`);
      if (ok) doDelete();
    } else {
      Alert.alert('Remover Certificação?', `Deseja remover "${certNameStr}" do seu perfil?`, [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Remover', style: 'destructive', onPress: doDelete },
      ]);
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

  const getEducationLevelOptions = () => [
    { label: 'Ensino Médio', value: '1' },
    { label: 'Graduação', value: '2' },
    { label: 'Mestrado', value: '3' },
    { label: 'Doutorado', value: '4' },
  ];

  if (!user) {
    return null;
  }

  const avatarPhoto = (user as any).avatar_photo;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Header with Avatar */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.avatarWrapper} onPress={handleChangePhoto}>
            {avatarPhoto ? (
              <Image source={{ uri: avatarPhoto }} style={styles.avatarImage} />
            ) : (
              <View style={[styles.avatarPlaceholder, { backgroundColor: user.avatar_color || '#4CAF50' }]}>
                <Ionicons name={(user.avatar_icon as any) || 'person'} size={48} color="#fff" />
              </View>
            )}
            <View style={styles.cameraIcon}>
              <Ionicons name="camera" size={16} color="#fff" />
            </View>
          </TouchableOpacity>

          <Text style={styles.name}>{user.name}</Text>
          <Text style={styles.email}>{user.email}</Text>

          <View style={styles.badges}>
            <View style={styles.levelBadge}>
              <Text style={styles.levelText}>Nível {user.level}</Text>
            </View>
            <View style={styles.moneyBadge}>
              <Text style={styles.moneyText}>R$ {(user.money || 0).toLocaleString('pt-BR')}</Text>
            </View>
          </View>

          {avatarPhoto && (
            <TouchableOpacity style={styles.removePhotoButton} onPress={handleRemovePhoto}>
              <Ionicons name="trash-outline" size={14} color="#F44336" />
              <Text style={styles.removePhotoText}>Remover foto</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Skills Section */}
        {user.skills && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Habilidades</Text>
            <View style={styles.skillsGrid}>
              {Object.entries(user.skills).map(([skill, value]: [string, any]) => (
                <View key={skill} style={styles.skillItem}>
                  <View style={styles.skillLabelRow}>
                    <Text style={styles.skillName}>
                      {skill.charAt(0).toUpperCase() + skill.slice(1)}
                    </Text>
                    <Text style={styles.skillValue}>{value}/10</Text>
                  </View>
                  <View style={styles.skillBarBg}>
                    <View style={[styles.skillBarFill, { width: `${(value / 10) * 100}%` }]} />
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Education Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="school" size={22} color="#2196F3" />
            <Text style={styles.sectionTitle}>Educação</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => setShowEducationModal(true)}
            >
              <Ionicons name="add" size={20} color="#fff" />
              <Text style={styles.addButtonText}>Adicionar</Text>
            </TouchableOpacity>
          </View>
          {user.education && user.education.length > 0 ? (
            user.education.map((edu: any) => (
              <View key={edu.id} style={styles.card}>
                <View style={styles.cardIcon}>
                  <Ionicons name="school" size={24} color="#2196F3" />
                </View>
                <View style={styles.cardContent}>
                  <Text style={styles.cardTitle}>{edu.degree}</Text>
                  <Text style={styles.cardSubtitle}>{edu.field}</Text>
                  <Text style={styles.cardInfo}>
                    {edu.institution} - {edu.year_completed}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => handleDeleteEducation(edu.id, edu.degree)}
                >
                  <Ionicons name="close-circle" size={24} color="#F44336" />
                </TouchableOpacity>
              </View>
            ))
          ) : (
            <View style={styles.emptyCard}>
              <Ionicons name="school-outline" size={32} color="#555" />
              <Text style={styles.emptyText}>Nenhuma educação adicionada</Text>
              <Text style={styles.emptySubtext}>Adicione educação para ganhar XP e desbloquear vagas</Text>
            </View>
          )}
        </View>

        {/* Certifications Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="ribbon" size={22} color="#FF9800" />
            <Text style={styles.sectionTitle}>Certificações</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => setShowCertModal(true)}
            >
              <Ionicons name="add" size={20} color="#fff" />
              <Text style={styles.addButtonText}>Adicionar</Text>
            </TouchableOpacity>
          </View>
          {user.certifications && user.certifications.length > 0 ? (
            user.certifications.map((cert: any) => (
              <View key={cert.id} style={styles.card}>
                <View style={styles.cardIcon}>
                  <Ionicons name="ribbon" size={24} color="#FF9800" />
                </View>
                <View style={styles.cardContent}>
                  <Text style={styles.cardTitle}>{cert.name}</Text>
                  <Text style={styles.cardSubtitle}>{cert.issuer}</Text>
                  <Text style={styles.cardInfo}>Boost: +{cert.skill_boost} habilidades</Text>
                </View>
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => handleDeleteCertification(cert.id, cert.name)}
                >
                  <Ionicons name="close-circle" size={24} color="#F44336" />
                </TouchableOpacity>
              </View>
            ))
          ) : (
            <View style={styles.emptyCard}>
              <Ionicons name="ribbon-outline" size={32} color="#555" />
              <Text style={styles.emptyText}>Nenhuma certificação adicionada</Text>
              <Text style={styles.emptySubtext}>Certificações aumentam suas habilidades</Text>
            </View>
          )}
        </View>

        {/* Work Experience Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="briefcase" size={22} color="#9C27B0" />
            <Text style={styles.sectionTitle}>Experiência</Text>
          </View>
          {user.work_experience && user.work_experience.length > 0 ? (
            user.work_experience.map((exp: any) => (
              <View key={exp.id} style={styles.card}>
                <View style={styles.cardIcon}>
                  <Ionicons name="briefcase" size={24} color="#9C27B0" />
                </View>
                <View style={styles.cardContent}>
                  <Text style={styles.cardTitle}>{exp.position}</Text>
                  <Text style={styles.cardSubtitle}>{exp.company}</Text>
                  <Text style={styles.cardInfo}>
                    R$ {exp.salary?.toLocaleString('pt-BR') || '0'}/mês
                    {exp.is_current && (
                      <Text style={styles.currentBadge}> (Atual)</Text>
                    )}
                  </Text>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyCard}>
              <Ionicons name="briefcase-outline" size={32} color="#555" />
              <Text style={styles.emptyText}>Nenhuma experiência ainda</Text>
              <Text style={styles.emptySubtext}>Candidate-se a vagas na aba Empregos</Text>
            </View>
          )}
        </View>

        {/* Personal Data Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="person-circle" size={22} color="#4CAF50" />
            <Text style={styles.sectionTitle}>Dados Pessoais</Text>
            <TouchableOpacity style={styles.addButton} onPress={openPersonalData}>
              <Ionicons name="create" size={20} color="#fff" />
              <Text style={styles.addButtonText}>Editar</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.cardContent}>
              <View style={{ gap: 6 }}>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <Ionicons name="person" size={16} color="#888" />
                  <Text style={styles.personalLabel}>{(user as any)?.full_name || user?.name || 'Não informado'}</Text>
                </View>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <Ionicons name="mail" size={16} color="#888" />
                  <Text style={styles.personalLabel}>{user?.email || 'Não informado'}</Text>
                </View>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <Ionicons name="call" size={16} color="#888" />
                  <Text style={styles.personalLabel}>{(user as any)?.phone || 'Não informado'}</Text>
                </View>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <Ionicons name="location" size={16} color="#888" />
                  <Text style={styles.personalLabel}>
                    {(user as any)?.address ? `${(user as any).address}, ${(user as any).city || ''} - ${(user as any).state || ''}` : 'Não informado'}
                  </Text>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* PIX Key Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="wallet" size={22} color="#FFD700" />
            <Text style={styles.sectionTitle}>Chave PIX (Premiação Real)</Text>
            <TouchableOpacity style={[styles.addButton, { backgroundColor: '#FFD700' }]} onPress={openPixModal}>
              <Ionicons name="create" size={20} color="#000" />
              <Text style={[styles.addButtonText, { color: '#000' }]}>{(user as any)?.pix_key ? 'Editar' : 'Cadastrar'}</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.cardContent}>
              {(user as any)?.pix_key ? (
                <View style={{ gap: 6 }}>
                  <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
                    <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                    <Text style={styles.personalLabel}>Chave: {(user as any).pix_key}</Text>
                  </View>
                  <Text style={{ color: '#888', fontSize: 12 }}>Tipo: {(user as any).pix_type || 'CPF'}</Text>
                </View>
              ) : (
                <View style={{ gap: 6, alignItems: 'center' }}>
                  <Ionicons name="alert-circle" size={24} color="#FF9800" />
                  <Text style={{ color: '#FF9800', fontSize: 13, textAlign: 'center' }}>
                    Cadastre sua chave PIX para receber prêmios em dinheiro real!
                  </Text>
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out" size={24} color="#F44336" />
          <Text style={styles.logoutText}>Sair</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Photo Preview Modal */}
      <Modal
        visible={showPhotoModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => { setShowPhotoModal(false); setNewPhoto(null); }}
      >
        <View style={styles.photoModalOverlay}>
          <View style={styles.photoModalContent}>
            <Text style={styles.photoModalTitle}>Nova Foto de Perfil</Text>

            {newPhoto && (
              <Image source={{ uri: newPhoto }} style={styles.photoPreview} />
            )}

            <Text style={styles.photoModalSubtext}>
              A foto foi cortada e ajustada automaticamente
            </Text>

            <View style={styles.photoModalButtons}>
              <TouchableOpacity
                style={styles.photoCancelButton}
                onPress={() => { setShowPhotoModal(false); setNewPhoto(null); }}
              >
                <Text style={styles.photoCancelText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.photoSaveButton, savingPhoto && styles.buttonDisabled]}
                onPress={handleSavePhoto}
                disabled={savingPhoto}
              >
                <Text style={styles.photoSaveText}>
                  {savingPhoto ? 'Salvando...' : 'Salvar'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Education Modal */}
      <Modal
        visible={showEducationModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowEducationModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalOverlay}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Adicionar Educação</Text>
              <TouchableOpacity onPress={() => setShowEducationModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.label}>Grau</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Graduação em..."
                placeholderTextColor="#666"
                value={eduDegree}
                onChangeText={setEduDegree}
              />

              <Text style={styles.label}>Área/Campo</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Administração, Tecnologia..."
                placeholderTextColor="#666"
                value={eduField}
                onChangeText={setEduField}
              />

              <Text style={styles.label}>Instituição</Text>
              <TextInput
                style={styles.input}
                placeholder="Nome da universidade/escola"
                placeholderTextColor="#666"
                value={eduInstitution}
                onChangeText={setEduInstitution}
              />

              <Text style={styles.label}>Ano de Conclusão</Text>
              <TextInput
                style={styles.input}
                placeholder="2024"
                placeholderTextColor="#666"
                value={eduYear}
                onChangeText={setEduYear}
                keyboardType="number-pad"
              />

              <Text style={styles.label}>Nível</Text>
              <View style={styles.levelSelector}>
                {getEducationLevelOptions().map(opt => (
                  <TouchableOpacity
                    key={opt.value}
                    style={[
                      styles.levelOption,
                      eduLevel === opt.value && styles.levelOptionActive,
                    ]}
                    onPress={() => setEduLevel(opt.value)}
                  >
                    <Text
                      style={[
                        styles.levelOptionText,
                        eduLevel === opt.value && styles.levelOptionTextActive,
                      ]}
                    >
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={styles.submitButton} onPress={handleAddEducation}>
                <Text style={styles.submitButtonText}>Adicionar Educação</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Certification Modal */}
      <Modal
        visible={showCertModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCertModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalOverlay}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Adicionar Certificação</Text>
              <TouchableOpacity onPress={() => setShowCertModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.label}>Nome da Certificação</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: PMP, AWS Certified..."
                placeholderTextColor="#666"
                value={certName}
                onChangeText={setCertName}
              />

              <Text style={styles.label}>Emissor</Text>
              <TextInput
                style={styles.input}
                placeholder="Organização que emitiu"
                placeholderTextColor="#666"
                value={certIssuer}
                onChangeText={setCertIssuer}
              />

              <Text style={styles.label}>Boost de Habilidade (1-10)</Text>
              <View style={styles.boostSelector}>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                  <TouchableOpacity
                    key={num}
                    style={[
                      styles.boostOption,
                      certBoost === String(num) && styles.boostOptionActive,
                    ]}
                    onPress={() => setCertBoost(String(num))}
                  >
                    <Text
                      style={[
                        styles.boostOptionText,
                        certBoost === String(num) && styles.boostOptionTextActive,
                      ]}
                    >
                      {num}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={styles.submitButton} onPress={handleAddCertification}>
                <Text style={styles.submitButtonText}>Adicionar Certificação</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Personal Data Modal */}
      <Modal visible={showPersonalModal} animationType="slide" transparent onRequestClose={() => setShowPersonalModal(false)}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Dados Pessoais</Text>
                <TouchableOpacity onPress={() => setShowPersonalModal(false)}>
                  <Ionicons name="close" size={28} color="#fff" />
                </TouchableOpacity>
              </View>
              <ScrollView style={{ maxHeight: 420 }}>
                <Text style={styles.inputLabel}>Nome Completo</Text>
                <TextInput style={styles.input} value={personalData.full_name} onChangeText={v => setPersonalData(p => ({...p, full_name: v}))} placeholder="Nome completo" placeholderTextColor="#666" />

                <Text style={styles.inputLabel}>Telefone Celular</Text>
                <TextInput style={styles.input} value={personalData.phone} onChangeText={v => setPersonalData(p => ({...p, phone: v}))} placeholder="(11) 99999-9999" placeholderTextColor="#666" keyboardType="phone-pad" />

                <Text style={styles.inputLabel}>Endereço</Text>
                <TextInput style={styles.input} value={personalData.address} onChangeText={v => setPersonalData(p => ({...p, address: v}))} placeholder="Rua, número, complemento" placeholderTextColor="#666" />

                <Text style={styles.inputLabel}>Cidade</Text>
                <TextInput style={styles.input} value={personalData.city} onChangeText={v => setPersonalData(p => ({...p, city: v}))} placeholder="Cidade" placeholderTextColor="#666" />

                <View style={{ flexDirection: 'row', gap: 12 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.inputLabel}>Estado</Text>
                    <TextInput style={styles.input} value={personalData.state} onChangeText={v => setPersonalData(p => ({...p, state: v}))} placeholder="UF" placeholderTextColor="#666" maxLength={2} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.inputLabel}>CEP</Text>
                    <TextInput style={styles.input} value={personalData.zip_code} onChangeText={v => setPersonalData(p => ({...p, zip_code: v}))} placeholder="00000-000" placeholderTextColor="#666" keyboardType="numeric" />
                  </View>
                </View>

                <TouchableOpacity style={[styles.submitButton, savingPersonal && { opacity: 0.5 }]} onPress={handleSavePersonalData} disabled={savingPersonal}>
                  <Text style={styles.submitButtonText}>{savingPersonal ? 'Salvando...' : 'Salvar Dados'}</Text>
                </TouchableOpacity>
              </ScrollView>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* PIX Modal */}
      <Modal visible={showPixModal} animationType="slide" transparent onRequestClose={() => setShowPixModal(false)}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Chave PIX</Text>
                <TouchableOpacity onPress={() => setShowPixModal(false)}>
                  <Ionicons name="close" size={28} color="#fff" />
                </TouchableOpacity>
              </View>
              <Text style={{ color: '#FFD700', fontSize: 13, marginBottom: 16 }}>
                Configure sua chave PIX para receber premiações em dinheiro real dos rankings mensais.
              </Text>

              <Text style={styles.inputLabel}>Tipo de Chave</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 16 }}>
                {[
                  { key: 'cpf', label: 'CPF' },
                  { key: 'email', label: 'E-mail' },
                  { key: 'phone', label: 'Telefone' },
                  { key: 'random', label: 'Aleatória' },
                ].map(t => (
                  <TouchableOpacity
                    key={t.key}
                    style={[
                      { flex: 1, paddingVertical: 10, borderRadius: 8, alignItems: 'center', backgroundColor: '#2a2a2a', borderWidth: 1, borderColor: '#3a3a3a' },
                      pixType === t.key && { backgroundColor: '#FFD700', borderColor: '#FFD700' },
                    ]}
                    onPress={() => setPixType(t.key)}
                  >
                    <Text style={[{ color: '#888', fontSize: 12, fontWeight: 'bold' }, pixType === t.key && { color: '#000' }]}>{t.label}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.inputLabel}>Chave PIX</Text>
              <TextInput
                style={styles.input}
                placeholder={pixType === 'cpf' ? '000.000.000-00' : pixType === 'email' ? 'email@exemplo.com' : pixType === 'phone' ? '+55 (11) 99999-9999' : 'Cole sua chave aleatória'}
                placeholderTextColor="#555"
                value={pixKey}
                onChangeText={setPixKey}
                keyboardType={pixType === 'phone' ? 'phone-pad' : pixType === 'email' ? 'email-address' : 'default'}
              />

              <TouchableOpacity
                style={[styles.saveButton, { backgroundColor: '#FFD700' }, savingPix && { opacity: 0.5 }]}
                onPress={handleSavePix}
                disabled={savingPix}
              >
                <Text style={[styles.saveButtonText, { color: '#000' }]}>{savingPix ? 'Salvando...' : 'Salvar Chave PIX'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
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
    paddingBottom: 32,
  },

  // Header
  header: {
    alignItems: 'center',
    paddingVertical: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
    marginBottom: 24,
  },
  avatarWrapper: {
    position: 'relative',
    marginBottom: 16,
  },
  avatarImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: '#4CAF50',
  },
  avatarPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#4CAF50',
  },
  cameraIcon: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#4CAF50',
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#1a1a1a',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    color: '#888',
    marginBottom: 12,
  },
  badges: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
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
    fontSize: 14,
  },
  moneyBadge: {
    backgroundColor: '#2a3a2a',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  moneyText: {
    color: '#4CAF50',
    fontWeight: 'bold',
    fontSize: 14,
  },
  removePhotoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
    paddingVertical: 4,
  },
  removePhotoText: {
    fontSize: 12,
    color: '#F44336',
  },

  // Skills
  skillsGrid: {
    gap: 12,
  },
  skillItem: {
    gap: 4,
  },
  skillLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  skillName: {
    fontSize: 14,
    color: '#ccc',
  },
  skillValue: {
    fontSize: 14,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  skillBarBg: {
    height: 6,
    backgroundColor: '#3a3a3a',
    borderRadius: 3,
    overflow: 'hidden',
  },
  skillBarFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 3,
  },

  // Sections
  section: {
    marginBottom: 24,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 4,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: 'bold',
  },

  // Cards
  card: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardIcon: {
    marginRight: 12,
  },
  cardContent: {
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
    marginBottom: 2,
  },
  cardInfo: {
    fontSize: 12,
    color: '#666',
  },
  currentBadge: {
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  deleteButton: {
    padding: 4,
    marginLeft: 8,
  },
  personalLabel: {
    color: '#ccc',
    fontSize: 14,
    flex: 1,
  },

  // Empty State
  emptyCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#3a3a3a',
    borderStyle: 'dashed',
  },
  emptyText: {
    color: '#666',
    fontSize: 16,
    fontWeight: 'bold',
  },
  emptySubtext: {
    color: '#555',
    fontSize: 13,
    textAlign: 'center',
  },

  // Logout
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    gap: 8,
  },
  logoutText: {
    color: '#F44336',
    fontSize: 18,
    fontWeight: 'bold',
  },

  // Photo Modal
  photoModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  photoModalContent: {
    backgroundColor: '#2a2a2a',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 360,
    alignItems: 'center',
  },
  photoModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
  },
  photoPreview: {
    width: 200,
    height: 200,
    borderRadius: 100,
    marginBottom: 16,
    borderWidth: 3,
    borderColor: '#4CAF50',
  },
  photoModalSubtext: {
    fontSize: 13,
    color: '#888',
    marginBottom: 20,
    textAlign: 'center',
  },
  photoModalButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  photoCancelButton: {
    flex: 1,
    backgroundColor: '#3a3a3a',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  photoCancelText: {
    color: '#aaa',
    fontSize: 16,
    fontWeight: 'bold',
  },
  photoSaveButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  photoSaveText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonDisabled: {
    opacity: 0.6,
  },

  // Modal
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
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 22,
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
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },

  // Level Selector
  levelSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  levelOption: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#2a2a2a',
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },
  levelOptionActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  levelOptionText: {
    color: '#888',
    fontSize: 13,
    fontWeight: 'bold',
  },
  levelOptionTextActive: {
    color: '#fff',
  },

  // Boost Selector
  boostSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  boostOption: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },
  boostOptionActive: {
    backgroundColor: '#FF9800',
    borderColor: '#FF9800',
  },
  boostOptionText: {
    color: '#888',
    fontSize: 14,
    fontWeight: 'bold',
  },
  boostOptionTextActive: {
    color: '#fff',
  },

  submitButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 24,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
