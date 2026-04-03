import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const showMsg = (title: string, msg: string) => {
  if (Platform.OS === 'web') window.alert(`${title}\n${msg}`);
  else {
    const { Alert } = require('react-native');
    Alert.alert(title, msg);
  }
};

export default function VerifyEmail() {
  const router = useRouter();
  const { user, token, refreshUser } = useAuth();
  const { t } = useLanguage();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (user?.email) sendCode();
  }, []);

  const sendCode = async () => {
    if (!user?.email) return;
    setSending(true);
    try {
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/send-verification`, {
        email: user.email
      });
    } catch (e) {
      console.error('Send verification error:', e);
    } finally { setSending(false); }
  };

  const handleVerify = async () => {
    if (!code || code.length !== 6) { showMsg(t('general.error'), t('auth.invalidCode')); return; }
    setLoading(true);
    try {
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/verify-email`, {
        email: user?.email, code
      });
      showMsg(t('general.success'), t('auth.emailVerified'));
      await refreshUser();
      router.replace('/(tabs)/home');
    } catch (e: any) {
      showMsg(t('general.error'), e.response?.data?.detail || t('auth.invalidCode'));
    } finally { setLoading(false); }
  };

  const handleSkip = () => {
    router.replace('/(tabs)/home');
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={s.container}>
      <View style={s.content}>
        <Ionicons name="mail-unread" size={80} color="#4CAF50" />
        <Text style={s.title}>{t('auth.verifyYourEmail')}</Text>
        <Text style={s.subtitle}>{t('auth.verifyEmailHint')}</Text>
        <Text style={s.email}>{user?.email}</Text>

        <View style={s.codeWrap}>
          <TextInput style={s.codeInput} placeholder="000000" placeholderTextColor="#555"
            value={code} onChangeText={setCode} keyboardType="number-pad" maxLength={6}
            textAlign="center" />
        </View>

        <TouchableOpacity style={[s.btn, loading && s.btnDisabled]} onPress={handleVerify} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{t('auth.verifyCode')}</Text>}
        </TouchableOpacity>

        <TouchableOpacity onPress={sendCode} disabled={sending} style={s.resend}>
          <Text style={s.resendText}>{sending ? t('general.loading') : t('auth.resendCode')}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={handleSkip} style={s.skip}>
          <Text style={s.skipText}>{t('auth.skipForNow')}</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  title: { fontSize: 26, fontWeight: 'bold', color: '#fff', marginTop: 20 },
  subtitle: { fontSize: 14, color: '#aaa', textAlign: 'center', marginTop: 8, lineHeight: 20 },
  email: { fontSize: 16, color: '#4CAF50', fontWeight: '600', marginTop: 4 },
  codeWrap: { width: '100%', marginTop: 32 },
  codeInput: { backgroundColor: '#1e1e1e', borderRadius: 12, borderWidth: 2, borderColor: '#333', height: 60, fontSize: 28, color: '#fff', letterSpacing: 12, fontWeight: 'bold' },
  btn: { width: '100%', backgroundColor: '#4CAF50', borderRadius: 12, height: 52, justifyContent: 'center', alignItems: 'center', marginTop: 20 },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  resend: { marginTop: 16 },
  resendText: { color: '#4CAF50', fontSize: 14 },
  skip: { marginTop: 24 },
  skipText: { color: '#666', fontSize: 14 },
});
