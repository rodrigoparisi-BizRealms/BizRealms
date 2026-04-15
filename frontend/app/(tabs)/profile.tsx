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
import { useLanguage } from '../../context/LanguageContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import * as ImagePicker from 'expo-image-picker';
import { useAds } from '../../context/AdContext';
import { useSound } from '../../context/SoundContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

import { useTheme } from '../../context/ThemeContext';

export default function Profile() {
  const { user, token, logout, refreshUser, biometricEnabled, biometricAvailable, toggleBiometric } = useAuth();
  const { locale, setLocale, languages, t, formatMoney } = useLanguage();
  const { isDark, colors, toggleTheme } = useTheme();
  const { showAd } = useAds();
  const { playClick, playSuccess, soundEnabled, toggleSound } = useSound();
  const router = useRouter();
  const [showEducationModal, setShowEducationModal] = useState(false);
  const [showCertModal, setShowCertModal] = useState(false);
  const [showPhotoModal, setShowPhotoModal] = useState(false);
  const [showLangPicker, setShowLangPicker] = useState(false);
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
    identity_document: '',
    country: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    phone: '',
  });
  const [savingPersonal, setSavingPersonal] = useState(false);

  // PayPal account form
  const [showPaypalModal, setShowPaypalModal] = useState(false);
  const [paypalEmail, setPaypalEmail] = useState('');
  const [savingPaypal, setSavingPaypal] = useState(false);
  const [showPaypalInfo, setShowPaypalInfo] = useState(false);

  const showAlert = (title: string, msg: string) => {
    if (Platform.OS === 'web') window.alert(`${title}\n\n${msg}`);
    else Alert.alert(title, msg);
  };

  const openPersonalData = () => {
    setPersonalData({
      full_name: (user as any)?.full_name || user?.name || '',
      identity_document: (user as any)?.identity_document || '',
      country: (user as any)?.country || '',
      address: (user as any)?.address || '',
      city: (user as any)?.city || '',
      state: (user as any)?.state || '',
      zip_code: (user as any)?.zip_code || '',
      phone: (user as any)?.phone || '',
    });
    setShowPersonalModal(true);
  };

  const handleSavePersonalData = async () => {
    // Validate required fields
    const required = [
      { field: 'full_name', label: t('profile.personalFullName') || 'Nome completo' },
      { field: 'identity_document', label: t('profile.identityDocument') || 'Documento de Identidade' },
      { field: 'country', label: t('profile.country') || 'País' },
      { field: 'phone', label: t('profile.personalPhone') || 'Telefone' },
      { field: 'address', label: t('profile.personalAddress') || 'Endereço' },
      { field: 'city', label: t('profile.personalCity') || 'Cidade' },
      { field: 'state', label: t('profile.personalState') || 'Estado' },
      { field: 'zip_code', label: t('profile.personalZip') || 'CEP/Código Postal' },
    ];
    const missing = required.filter(r => !(personalData as any)[r.field]?.trim());
    if (missing.length > 0) {
      showAlert(t('profile.requiredFields') || 'Campos obrigatórios', `${t('profile.fillAllFields') || 'Preencha todos os campos'}:\n${missing.map(m => '• ' + m.label).join('\n')}`);
      return;
    }
    setSavingPersonal(true);
    try {
      await axios.put(
        `${EXPO_PUBLIC_BACKEND_URL}/api/user/personal-data`,
        personalData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      showAlert(t('general.success'), t('profile.dataSaved') || 'Personal data saved successfully');
      await refreshUser();
      setShowPersonalModal(false);
    } catch (e: any) {
      showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setSavingPersonal(false); }
  };

  const openPaypalModal = () => {
    setPaypalEmail((user as any)?.paypal_email || '');
    setShowPaypalModal(true);
  };

  const handleSavePaypal = async () => {
    if (!paypalEmail.trim()) { showAlert(t('general.error'), t('profile.paypalEmpty') || 'Enter your PayPal email'); return; }
    if (!paypalEmail.includes('@') || !paypalEmail.includes('.')) { showAlert(t('general.error'), t('profile.paypalInvalid') || 'Invalid email'); return; }
    // Require personal data (name + identity document) before PayPal
    const userName = (user as any)?.full_name || '';
    const userDoc = (user as any)?.identity_document || '';
    if (!userName.trim() || !userDoc.trim()) {
      showAlert(
        t('profile.paypalRequiresData') || 'Dados Pessoais Obrigatórios',
        t('profile.paypalRequiresDataMsg') || 'Para cadastrar sua conta PayPal, preencha primeiro seus Dados Pessoais (Nome Completo e Documento de Identidade).'
      );
      return;
    }
    setSavingPaypal(true);
    try {
      await axios.post(
        `${EXPO_PUBLIC_BACKEND_URL}/api/rewards/update-payment-info`,
        { method: 'paypal', paypal_email: paypalEmail },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      showAlert(t('general.success'), t('profile.paypalSaved') || 'PayPal account saved!');
      await refreshUser();
      setShowPaypalModal(false);
    } catch (e: any) {
      showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setSavingPaypal(false); }
  };

  const handleDeletePaypal = async () => {
    const doDelete = async () => {
      try {
        await axios.delete(
          `${EXPO_PUBLIC_BACKEND_URL}/api/rewards/delete-payment-info`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        showAlert(t('general.success'), t('profile.paypalRemoved') || 'PayPal account removed');
        setPaypalEmail('');
        await refreshUser();
      } catch (e: any) {
        showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
      }
    };
    if (Platform.OS === 'web') {
      if (window.confirm(t('profile.paypalRemoveConfirm') || 'Tem certeza que deseja remover sua conta PayPal?')) {
        await doDelete();
      }
    } else {
      Alert.alert(t('profile.removePaypal') || 'Remover PayPal', t('profile.paypalRemoveConfirm') || 'Tem certeza que deseja remover sua conta PayPal?', [
        { text: t('general.cancel'), style: 'cancel' },
        { text: 'Remover', style: 'destructive', onPress: doDelete },
      ]);
    }
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
      Alert.alert(t('general.error'), t('general.error'));
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

      Alert.alert(t('general.success'), t('general.success'));
      await refreshUser();
      setShowPhotoModal(false);
      setNewPhoto(null);
    } catch (error: any) {
      Alert.alert(t('general.error'), error.response?.data?.detail || t('general.error'));
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
        else Alert.alert(t('general.success'), t('general.success'));
        await refreshUser();
      } catch (error: any) {
        if (Platform.OS === 'web') window.alert(t('general.error'));
        else Alert.alert(t('general.error'), t('general.error'));
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
          { text: t('general.cancel'), style: 'cancel' },
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
        else Alert.alert(t('general.success'), t('general.success'));
        await refreshUser();
      } catch (error: any) {
        const msg = error.response?.data?.detail || 'Erro ao remover educação';
        if (Platform.OS === 'web') window.alert(`Erro: ${msg}`);
        else Alert.alert(t('general.error'), msg);
      }
    };

    if (Platform.OS === 'web') {
      const ok = window.confirm(`Remover Educação?\n\nDeseja remover "${eduName}" do seu perfil?`);
      if (ok) doDelete();
    } else {
      Alert.alert('Remover Educação?', `Deseja remover "${eduName}" do seu perfil?`, [
        { text: t('general.cancel'), style: 'cancel' },
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
        else Alert.alert(t('general.success'), t('general.success'));
        await refreshUser();
      } catch (error: any) {
        const msg = error.response?.data?.detail || 'Erro ao remover certificação';
        if (Platform.OS === 'web') window.alert(`Erro: ${msg}`);
        else Alert.alert(t('general.error'), msg);
      }
    };

    if (Platform.OS === 'web') {
      const ok = window.confirm(`Remover Certificação?\n\nDeseja remover "${certNameStr}" do seu perfil?`);
      if (ok) doDelete();
    } else {
      Alert.alert('Remover Certificação?', `Deseja remover "${certNameStr}" do seu perfil?`, [
        { text: t('general.cancel'), style: 'cancel' },
        { text: 'Remover', style: 'destructive', onPress: doDelete },
      ]);
    }
  };

  const handleAddEducation = async () => {
    if (!eduDegree || !eduField || !eduInstitution || !eduYear) {
      Alert.alert(t('general.error'), t('general.error'));
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
      Alert.alert(t('general.error'), error.response?.data?.detail || t('general.error'));
    }
  };

  const handleAddCertification = async () => {
    if (!certName || !certIssuer) {
      Alert.alert(t('general.error'), t('general.error'));
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
      Alert.alert(t('general.error'), error.response?.data?.detail || t('general.error'));
    }
  };

  const getEducationLevelOptions = () => [
    { label: 'Ensino Médio', value: '1' },
    { label: 'Graduação', value: '2' },
    { label: 'Mestrado', value: '3' },
    { label: 'Doutorado', value: '4' },
  ];

  const handleResetAccount = () => {
    const doReset = async () => {
      try {
        await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/user/reset-account`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        });
        showAlert('Conta Zerada', t('profile.accountResetSuccess') || 'Sua conta foi zerada com sucesso. Todos os dados do jogo foram reiniciados.');
        await refreshUser();
      } catch (e: any) {
        showAlert(t('general.error'), e.response?.data?.detail || t('general.error'));
      }
    };
    if (Platform.OS === 'web') {
      if (window.confirm(t('profile.resetConfirmMsg') || 'TEM CERTEZA que deseja ZERAR sua conta? Todos os seus dados do jogo (dinheiro, empresas, investimentos, patrimônio, empregos) serão apagados permanentemente. Esta ação NÃO pode ser desfeita!')) {
        doReset();
      }
    } else {
      Alert.alert(
        t('profile.resetAccount') || 'Zerar Conta',
        t('profile.resetConfirmMsg') || 'TEM CERTEZA que deseja ZERAR sua conta? Todos os seus dados do jogo serão apagados permanentemente. Esta ação NÃO pode ser desfeita!',
        [
          { text: t('general.cancel'), style: 'cancel' },
          { text: 'ZERAR TUDO', style: 'destructive', onPress: doReset },
        ]
      );
    }
  };

  if (!user) {
    return null;
  }

  const avatarPhoto = (user as any).avatar_photo;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Header with Avatar */}
        <View style={[styles.header, { backgroundColor: colors.card }]}>
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
              <Text style={styles.moneyText}>{formatMoney(user.money || 0)}</Text>
            </View>
          </View>

          {avatarPhoto && (
            <TouchableOpacity style={styles.removePhotoButton} onPress={handleRemovePhoto}>
              <Ionicons name="trash-outline" size={14} color="#F44336" />
              <Text style={styles.removePhotoText}>{t('profile.removePhoto')}</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Skills Section */}
        {user.skills && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('profile.skills')}</Text>
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
            <Text style={styles.sectionTitle}>{t('profile.education')}</Text>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => setShowEducationModal(true)}
            >
              <Ionicons name="add" size={20} color="#fff" />
              <Text style={styles.addButtonText}>{t('profile.add')}</Text>
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
              <Text style={styles.emptyText}>{t('profile.noEducation')}</Text>
              <Text style={styles.emptySubtext}>{t('profile.noEducationHint')}</Text>
            </View>
          )}
        </View>

        {/* Certifications Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="ribbon" size={22} color="#FF9800" />
            <Text style={styles.sectionTitle}>{t('profile.certifications')}</Text>
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
              <Text style={styles.emptyText}>{t('profile.noCert')}</Text>
              <Text style={styles.emptySubtext}>{t('profile.noCertHint')}</Text>
            </View>
          )}
        </View>

        {/* Work Experience Section - Summary */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="briefcase" size={22} color="#9C27B0" />
            <Text style={styles.sectionTitle}>{t('profile.experience')}</Text>
          </View>
          {user.work_experience && user.work_experience.length > 0 ? (
            <View style={styles.card}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14 }}>
                <View style={{ width: 52, height: 52, borderRadius: 14, backgroundColor: '#9C27B025', justifyContent: 'center', alignItems: 'center' }}>
                  <Ionicons name="briefcase" size={26} color="#9C27B0" />
                </View>
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>
                    {user.work_experience.length} {user.work_experience.length === 1 ? 'emprego' : 'empregos'}
                  </Text>
                  {(() => {
                    const currentJob = user.work_experience.find((e: any) => e.is_current);
                    const totalSalary = user.work_experience.reduce((s: number, e: any) => s + (e.salary || 0), 0);
                    const totalXp = user.work_experience.reduce((s: number, e: any) => s + (e.experience_gained || 0), 0);
                    return (
                      <>
                        {currentJob && (
                          <Text style={{ color: '#4CAF50', fontSize: 13, fontWeight: '600' }}>
                            Atual: {currentJob.position} — {currentJob.company}
                          </Text>
                        )}
                        <View style={{ flexDirection: 'row', gap: 16, marginTop: 2 }}>
                          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                            <Ionicons name="cash" size={14} color="#FFD700" />
                            <Text style={{ color: '#aaa', fontSize: 12 }}>
                              $ {totalSalary.toLocaleString('en-US')}/mês total
                            </Text>
                          </View>
                          {totalXp > 0 && (
                            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                              <Ionicons name="star" size={14} color="#FF9800" />
                              <Text style={{ color: '#aaa', fontSize: 12 }}>
                                {totalXp.toLocaleString('en-US')} XP
                              </Text>
                            </View>
                          )}
                        </View>
                      </>
                    );
                  })()}
                </View>
              </View>
            </View>
          ) : (
            <View style={styles.emptyCard}>
              <Ionicons name="briefcase-outline" size={32} color="#555" />
              <Text style={styles.emptyText}>{t('profile.noExperience')}</Text>
              <Text style={styles.emptySubtext}>{t('profile.noExperienceHint')}</Text>
            </View>
          )}
        </View>

        {/* Personal Data Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="person-circle" size={22} color="#4CAF50" />
            <Text style={styles.sectionTitle}>{t('profile.personalData')}</Text>
            <TouchableOpacity style={styles.addButton} onPress={openPersonalData}>
              <Ionicons name="create" size={20} color="#fff" />
              <Text style={styles.addButtonText}>{t('profile.edit')}</Text>
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

        {/* Language Section - Dropdown Picker */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="language" size={22} color="#2196F3" />
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.language') || 'Idioma'}</Text>
          </View>
          <TouchableOpacity
            style={[styles.card, { backgroundColor: colors.card, borderColor: colors.cardBorder, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 }]}
            onPress={() => { playClick(); setShowLangPicker(!showLangPicker); }}
            activeOpacity={0.7}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <Text style={{ fontSize: 24 }}>{languages.find(l => l.code === locale)?.flag || '🌐'}</Text>
              <View>
                <Text style={{ color: colors.text, fontSize: 15, fontWeight: '600' }}>{languages.find(l => l.code === locale)?.name || 'Selecione'}</Text>
                <Text style={{ color: colors.textSecondary, fontSize: 12 }}>{t('profile.selectLanguage') || 'Toque para alterar idioma'}</Text>
              </View>
            </View>
            <Ionicons name={showLangPicker ? 'chevron-up' : 'chevron-down'} size={20} color={colors.textSecondary} />
          </TouchableOpacity>
          {showLangPicker && (
            <View style={{
              marginTop: 8,
              backgroundColor: colors.card,
              borderColor: colors.cardBorder,
              borderWidth: 1,
              borderRadius: 12,
              overflow: 'hidden',
              flexDirection: 'column',
            }}>
              {languages.map((lang, idx) => (
                <TouchableOpacity
                  key={lang.code}
                  style={{
                    flexDirection: 'row', alignItems: 'center', gap: 12,
                    paddingHorizontal: 16, paddingVertical: 14,
                    backgroundColor: locale === lang.code ? (isDark ? '#1a2a4a' : '#E3F2FD') : 'transparent',
                    borderBottomWidth: idx < languages.length - 1 ? 1 : 0,
                    borderBottomColor: isDark ? '#2a2a2a' : '#e0e0e0',
                  }}
                  onPress={() => { playClick(); setLocale(lang.code); setShowLangPicker(false); }}
                >
                  <Text style={{ fontSize: 24 }}>{lang.flag}</Text>
                  <Text style={{ color: locale === lang.code ? '#2196F3' : colors.text, fontSize: 15, fontWeight: locale === lang.code ? 'bold' : 'normal', flex: 1 }}>{lang.name}</Text>
                  {locale === lang.code && <Ionicons name="checkmark-circle" size={20} color="#2196F3" />}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Theme Toggle Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name={isDark ? 'moon' : 'sunny'} size={22} color={isDark ? '#9C27B0' : '#FF9800'} />
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.theme') || 'Tema'}</Text>
          </View>
          <TouchableOpacity
            style={[styles.card, { backgroundColor: colors.card, borderColor: colors.cardBorder, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 }]}
            onPress={() => { playClick(); toggleTheme(); }}
            activeOpacity={0.7}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: isDark ? '#2a2a4a' : '#FFF3E0', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name={isDark ? 'moon' : 'sunny'} size={22} color={isDark ? '#BB86FC' : '#FF9800'} />
              </View>
              <View>
                <Text style={{ color: colors.text, fontSize: 15, fontWeight: '600' }}>{isDark ? (t('profile.darkMode') || 'Modo Escuro') : (t('profile.lightMode') || 'Modo Claro')}</Text>
                <Text style={{ color: colors.textSecondary, fontSize: 12 }}>{t('profile.tapToSwitch') || 'Toque para alternar'}</Text>
              </View>
            </View>
            <View style={{ width: 52, height: 30, borderRadius: 15, backgroundColor: isDark ? '#BB86FC' : '#FF9800', justifyContent: 'center', paddingHorizontal: 3 }}>
              <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: '#fff', alignSelf: isDark ? 'flex-end' : 'flex-start' }} />
            </View>
          </TouchableOpacity>
        </View>

        {/* Sound Effects Toggle */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name={soundEnabled ? 'volume-high' : 'volume-mute'} size={22} color={soundEnabled ? '#4CAF50' : '#888'} />
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.sounds') || 'Sons'}</Text>
          </View>
          <TouchableOpacity
            style={[styles.card, { backgroundColor: colors.card, borderColor: colors.cardBorder, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 }]}
            onPress={() => { playClick(); toggleSound(); }}
            activeOpacity={0.7}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: soundEnabled ? '#1a3a1a' : '#2a2a2a', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name={soundEnabled ? 'volume-high' : 'volume-mute'} size={22} color={soundEnabled ? '#4CAF50' : '#666'} />
              </View>
              <View>
                <Text style={{ color: colors.text, fontSize: 15, fontWeight: '600' }}>{t('profile.soundEffects') || 'Efeitos Sonoros'}</Text>
                <Text style={{ color: colors.textSecondary, fontSize: 12 }}>{soundEnabled ? (t('profile.soundOn') || 'Sons de clique ativados') : (t('profile.soundOff') || 'Sons desativados')}</Text>
              </View>
            </View>
            <View style={{ width: 52, height: 30, borderRadius: 15, backgroundColor: soundEnabled ? '#4CAF50' : '#444', justifyContent: 'center', paddingHorizontal: 3 }}>
              <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: '#fff', alignSelf: soundEnabled ? 'flex-end' : 'flex-start' }} />
            </View>
          </TouchableOpacity>
        </View>

        {/* Music Section removed - Player is now in the tab bar */}

        {/* Biometric / Security Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="finger-print" size={22} color="#2196F3" />
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.security') || 'Segurança'}</Text>
          </View>
          <TouchableOpacity
            style={[styles.card, { backgroundColor: colors.card, borderColor: colors.cardBorder, borderWidth: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 }]}
            onPress={biometricAvailable ? () => { playClick(); toggleBiometric(); } : undefined}
            activeOpacity={biometricAvailable ? 0.7 : 1}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
              <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: biometricEnabled ? '#1a3a4a' : '#2a2a2a', alignItems: 'center', justifyContent: 'center' }}>
                <Ionicons name="finger-print" size={22} color={biometricEnabled ? '#2196F3' : '#666'} />
              </View>
              <View>
                <Text style={{ color: colors.text, fontSize: 15, fontWeight: '600' }}>{t('profile.biometric') || 'Biometria / Face ID'}</Text>
                <Text style={{ color: colors.textSecondary, fontSize: 12 }}>{biometricAvailable ? (t('profile.biometricHint') || 'Proteja o acesso ao jogo') : (t('profile.biometricUnavailable') || 'Indisponível neste dispositivo')}</Text>
              </View>
            </View>
            <View style={{ width: 52, height: 30, borderRadius: 15, backgroundColor: biometricEnabled ? '#2196F3' : '#444', justifyContent: 'center', paddingHorizontal: 3, opacity: biometricAvailable ? 1 : 0.4 }}>
              <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: '#fff', alignSelf: biometricEnabled ? 'flex-end' : 'flex-start' }} />
            </View>
          </TouchableOpacity>
        </View>

        {/* PayPal Account Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="logo-paypal" size={22} color="#0070BA" />
            <Text style={styles.sectionTitle}>{t('profile.paypalAccount')}</Text>
            <TouchableOpacity
              style={{ marginLeft: 4, padding: 4 }}
              onPress={() => setShowPaypalInfo(true)}
            >
              <Ionicons name="help-circle" size={20} color="#0070BA" />
            </TouchableOpacity>
            <TouchableOpacity style={[styles.addButton, { backgroundColor: '#0070BA' }]} onPress={openPaypalModal}>
              <Ionicons name="create" size={20} color="#fff" />
              <Text style={[styles.addButtonText, { color: '#fff' }]}>{(user as any)?.paypal_email ? t('profile.edit') || 'Editar' : t('profile.register') || 'Cadastrar'}</Text>
            </TouchableOpacity>
          </View>
          
          {/* PayPal Info Tooltip */}
          {showPaypalInfo && (
            <View style={{ backgroundColor: '#0d2137', borderRadius: 12, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: '#0070BA33' }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Ionicons name="information-circle" size={18} color="#0070BA" />
                  <Text style={{ color: '#0070BA', fontSize: 15, fontWeight: 'bold' }}>{t('profile.howPaymentWorks')}</Text>
                </View>
                <TouchableOpacity onPress={() => setShowPaypalInfo(false)}>
                  <Ionicons name="close-circle" size={22} color="#666" />
                </TouchableOpacity>
              </View>
              <Text style={{ color: '#ccc', fontSize: 13, lineHeight: 20, marginBottom: 8 }}>
                {t('profile.paypalInfoText1')}
              </Text>
              <Text style={{ color: '#ccc', fontSize: 13, lineHeight: 20, marginBottom: 8 }}>
                {t('profile.paypalInfoText2')}
              </Text>
              <Text style={{ color: '#ccc', fontSize: 13, lineHeight: 20, marginBottom: 8 }}>
                {t('profile.paypalInfoText3')}
              </Text>
              <Text style={{ color: '#FF9800', fontSize: 12, fontStyle: 'italic', marginTop: 4 }}>
                {t('profile.paypalInfoNote')}
              </Text>
            </View>
          )}
          <View style={styles.card}>
            <View style={styles.cardContent}>
              {(user as any)?.paypal_email ? (
                <View style={{ gap: 8 }}>
                  <View style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
                    <Ionicons name="checkmark-circle" size={18} color="#4CAF50" />
                    <Text style={{ color: '#4CAF50', fontSize: 14, fontWeight: '600' }}>{t('profile.paypalConfigured') || 'Conta PayPal cadastrada'}</Text>
                  </View>
                  <View style={{ backgroundColor: '#1a2a3a', borderRadius: 10, padding: 12, gap: 6 }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text style={{ color: '#aaa', fontSize: 12 }}>E-mail</Text>
                      <Text style={{ color: '#fff', fontSize: 14, fontWeight: '600' }}>{(user as any).paypal_email}</Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 10, backgroundColor: '#2a1a1a', borderRadius: 10, marginTop: 4 }}
                    onPress={handleDeletePaypal}
                  >
                    <Ionicons name="trash" size={16} color="#F44336" />
                    <Text style={{ color: '#F44336', fontSize: 13, fontWeight: '600' }}>{t('profile.removePaypal') || 'Remover conta PayPal'}</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View style={{ gap: 6, alignItems: 'center' }}>
                  <Ionicons name="alert-circle" size={24} color="#FF9800" />
                  <Text style={{ color: '#FF9800', fontSize: 13, textAlign: 'center' }}>
                    {t('profile.paypalConfigHint') || 'Cadastre sua conta PayPal para receber premiação em dinheiro real!'}
                  </Text>
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Legal Links */}
        <View style={styles.legalSection}>
          <TouchableOpacity style={styles.legalLink} onPress={() => router.push('/legal/terms')}>
            <Ionicons name="document-text" size={20} color="#888" />
            <Text style={styles.legalLinkText}>{t('legal.terms')}</Text>
            <Ionicons name="chevron-forward" size={18} color="#555" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.legalLink} onPress={() => router.push('/legal/privacy')}>
            <Ionicons name="shield-checkmark" size={20} color="#888" />
            <Text style={styles.legalLinkText}>{t('legal.privacy')}</Text>
            <Ionicons name="chevron-forward" size={18} color="#555" />
          </TouchableOpacity>
        </View>

        {/* Reset Account Button */}
        <TouchableOpacity
          style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, backgroundColor: '#2a1a1a', borderRadius: 12, marginHorizontal: 16, marginBottom: 8 }}
          onPress={handleResetAccount}
        >
          <Ionicons name="refresh-circle" size={22} color="#FF9800" />
          <Text style={{ color: '#FF9800', fontSize: 15, fontWeight: '600' }}>{t('profile.resetAccount') || 'Zerar Conta'}</Text>
        </TouchableOpacity>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out" size={24} color="#F44336" />
          <Text style={styles.logoutText}>{t('profile.logout')}</Text>
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
            <Text style={styles.photoModalTitle}>{t('profile.newPhoto')}</Text>

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
              <Text style={styles.modalTitle}>{t('profile.addEducation')}</Text>
              <TouchableOpacity onPress={() => setShowEducationModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.label}>{t('profile.degree')}</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Graduação em..."
                placeholderTextColor="#666"
                value={eduDegree}
                onChangeText={setEduDegree}
              />

              <Text style={styles.label}>{t('profile.field')}</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Administração, Tecnologia..."
                placeholderTextColor="#666"
                value={eduField}
                onChangeText={setEduField}
              />

              <Text style={styles.label}>{t('profile.institution')}</Text>
              <TextInput
                style={styles.input}
                placeholder="Nome da universidade/escola"
                placeholderTextColor="#666"
                value={eduInstitution}
                onChangeText={setEduInstitution}
              />

              <Text style={styles.label}>{t('profile.yearCompleted')}</Text>
              <TextInput
                style={styles.input}
                placeholder="2024"
                placeholderTextColor="#666"
                value={eduYear}
                onChangeText={setEduYear}
                keyboardType="number-pad"
              />

              <Text style={styles.label}>{t('profile.levelLabel')}</Text>
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
              <Text style={styles.modalTitle}>{t('profile.addCert')}</Text>
              <TouchableOpacity onPress={() => setShowCertModal(false)}>
                <Ionicons name="close" size={28} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.label}>{t('profile.certName')}</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: PMP, AWS Certified..."
                placeholderTextColor="#666"
                value={certName}
                onChangeText={setCertName}
              />

              <Text style={styles.label}>{t('profile.issuer')}</Text>
              <TextInput
                style={styles.input}
                placeholder="Organização que emitiu"
                placeholderTextColor="#666"
                value={certIssuer}
                onChangeText={setCertIssuer}
              />

              <Text style={styles.label}>{t('profile.skillBoost')}</Text>
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
                <View style={{ backgroundColor: '#2a1a1a', borderRadius: 10, padding: 10, marginBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <Ionicons name="alert-circle" size={18} color="#FF9800" />
                  <Text style={{ color: '#FF9800', fontSize: 12, flex: 1 }}>Todos os campos são obrigatórios *</Text>
                </View>

                <Text style={styles.inputLabel}>{t('profile.personalFullName') || 'Nome Completo'} *</Text>
                <TextInput style={styles.input} value={personalData.full_name} onChangeText={v => setPersonalData(p => ({...p, full_name: v}))} placeholder="Nome completo" placeholderTextColor="#666" />

                <Text style={styles.inputLabel}>{t('profile.identityDocument') || 'Documento de Identidade'} *</Text>
                <TextInput style={styles.input} value={personalData.identity_document} onChangeText={v => setPersonalData(p => ({...p, identity_document: v}))} placeholder="CPF, RG, Passport, SSN..." placeholderTextColor="#666" />

                <Text style={styles.inputLabel}>{t('profile.country') || 'País'} *</Text>
                <TextInput style={styles.input} value={personalData.country} onChangeText={v => setPersonalData(p => ({...p, country: v}))} placeholder="Brasil, USA, Portugal..." placeholderTextColor="#666" />

                <Text style={styles.inputLabel}>{t('profile.personalPhone') || 'Telefone Celular'} *</Text>
                <TextInput style={styles.input} value={personalData.phone} onChangeText={v => setPersonalData(p => ({...p, phone: v}))} placeholder="(11) 99999-9999" placeholderTextColor="#666" keyboardType="phone-pad" />

                <Text style={styles.inputLabel}>{t('profile.personalAddress') || 'Endereço'} *</Text>
                <TextInput style={styles.input} value={personalData.address} onChangeText={v => setPersonalData(p => ({...p, address: v}))} placeholder="Rua, número, complemento" placeholderTextColor="#666" />

                <Text style={styles.inputLabel}>{t('profile.personalCity') || 'Cidade'} *</Text>
                <TextInput style={styles.input} value={personalData.city} onChangeText={v => setPersonalData(p => ({...p, city: v}))} placeholder="Cidade" placeholderTextColor="#666" />

                <View style={{ flexDirection: 'row', gap: 12 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.inputLabel}>{t('profile.personalState') || 'Estado/Região'} *</Text>
                    <TextInput style={styles.input} value={personalData.state} onChangeText={v => setPersonalData(p => ({...p, state: v}))} placeholder="SP, CA, London..." placeholderTextColor="#666" />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.inputLabel}>{t('profile.personalZip') || 'CEP/Postal'} *</Text>
                    <TextInput style={styles.input} value={personalData.zip_code} onChangeText={v => setPersonalData(p => ({...p, zip_code: v}))} placeholder="00000-000" placeholderTextColor="#666" />
                  </View>
                </View>

                <TouchableOpacity style={[styles.submitButton, savingPersonal && { opacity: 0.5 }]} onPress={handleSavePersonalData} disabled={savingPersonal}>
                  <Text style={styles.submitButtonText}>{savingPersonal ? 'Salvando...' : t('profile.saveData') || 'Salvar Dados'}</Text>
                </TouchableOpacity>
              </ScrollView>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* PayPal Modal */}
      <Modal visible={showPaypalModal} animationType="slide" transparent onRequestClose={() => setShowPaypalModal(false)}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>{t('profile.paypalAccount') || 'Conta PayPal'}</Text>
                <TouchableOpacity onPress={() => setShowPaypalModal(false)}>
                  <Ionicons name="close" size={28} color="#fff" />
                </TouchableOpacity>
              </View>
              <Text style={{ color: '#0070BA', fontSize: 13, marginBottom: 16 }}>
                {t('profile.paypalHint') || 'Configure sua conta PayPal para receber premiações em dinheiro real dos rankings mensais.'}
              </Text>

              <Text style={styles.inputLabel}>{t('profile.paypalEmailLabel') || 'E-mail PayPal'}</Text>
              <TextInput
                style={styles.input}
                placeholder="seuemail@exemplo.com"
                placeholderTextColor="#555"
                value={paypalEmail}
                onChangeText={setPaypalEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />

              <TouchableOpacity
                style={[styles.saveButton, { backgroundColor: '#0070BA' }, savingPaypal && { opacity: 0.5 }]}
                onPress={handleSavePaypal}
                disabled={savingPaypal}
              >
                <Text style={[styles.saveButtonText, { color: '#fff' }]}>{savingPaypal ? 'Salvando...' : t('profile.savePaypal') || 'Salvar Conta PayPal'}</Text>
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

  // Legal Links
  legalSection: {
    marginTop: 16,
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    overflow: 'hidden',
  },
  legalLink: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
    gap: 12,
  },
  legalLinkText: {
    flex: 1,
    color: '#ccc',
    fontSize: 15,
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
  inputLabel: {
    fontSize: 14,
    color: '#888',
    marginBottom: 6,
    marginTop: 12,
  },
  saveButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 16,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

// Music player styles
const mStyles = StyleSheet.create({
  toggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#2a2a2a',
    borderWidth: 1,
    borderColor: '#3a3a3a',
  },
  toggleBtnActive: {
    backgroundColor: '#9C27B015',
    borderColor: '#9C27B050',
  },
  toggleText: { color: '#666', fontSize: 12, fontWeight: 'bold' },
  disabledCard: {
    backgroundColor: '#1e1e1e',
    borderRadius: 14,
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  disabledText: { color: '#555', fontSize: 14 },
  autoPlayInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 10,
    backgroundColor: '#2a2a2a',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  autoPlayText: { color: '#9C27B0', fontSize: 12, fontWeight: '600' },
  playerCard: {
    backgroundColor: '#1e1e1e',
    borderRadius: 14,
    overflow: 'hidden',
  },
  nowPlaying: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#2a2a2a',
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  npDot: { width: 8, height: 8, borderRadius: 4 },
  npName: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  npArtist: { color: '#888', fontSize: 11 },
  skipBtn: {
    width: 30,
    height: 30,
    borderRadius: 8,
    backgroundColor: '#3a3a3a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playPauseBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#9C27B0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stopBtn: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#2a1a1a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  trackIcon: {
    width: 38,
    height: 38,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackName: { color: '#fff', fontSize: 14, fontWeight: '600' },
  trackArtist: { color: '#777', fontSize: 11, marginTop: 2 },
  eqBars: { flexDirection: 'row', alignItems: 'flex-end', gap: 2, height: 18 },
  eqBar: { width: 3, borderRadius: 2 },
});
