import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { useLanguage } from '../../context/LanguageContext';
import { useTheme } from '../../context/ThemeContext';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const showMsg = (title: string, msg: string) => {
  if (Platform.OS === 'web') window.alert(`${title}\n${msg}`);
  else {
    const { Alert } = require('react-native');
    Alert.alert(title, msg);
  }
};

export default function ForgotPassword() {
  const router = useRouter();
  const { t } = useLanguage();
  const [step, setStep] = useState<'email' | 'code' | 'password'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendCode = async () => {
    if (!email) { showMsg(t('general.error'), t('auth.fillAllFields')); return; }
    setLoading(true);
    try {
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/forgot-password`, { email });
      showMsg(t('general.success'), t('auth.resetCodeSent'));
      setStep('code');
    } catch (e: any) {
      showMsg(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setLoading(false); }
  };

  const handleVerifyCode = async () => {
    if (!code || code.length !== 6) { showMsg(t('general.error'), t('auth.invalidCode')); return; }
    setLoading(true);
    try {
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/verify-reset-code`, { email, code });
      setStep('password');
    } catch (e: any) {
      showMsg(t('general.error'), e.response?.data?.detail || t('auth.invalidCode'));
    } finally { setLoading(false); }
  };

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) { showMsg(t('general.error'), t('auth.passwordTooShort')); return; }
    if (newPassword !== confirmPassword) { showMsg(t('general.error'), t('auth.passwordsDontMatch')); return; }
    setLoading(true);
    try {
      await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/reset-password`, {
        email, code, new_password: newPassword
      });
      showMsg(t('general.success'), t('auth.passwordResetSuccess'));
      router.replace('/(auth)/login');
    } catch (e: any) {
      showMsg(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>

        <Ionicons name="key" size={64} color="#4CAF50" style={{ alignSelf: 'center' }} />
        <Text style={s.title}>{t('auth.resetPassword')}</Text>
        <Text style={s.subtitle}>
          {step === 'email' ? t('auth.resetEmailHint') :
           step === 'code' ? t('auth.resetCodeHint') :
           t('auth.resetNewPasswordHint')}
        </Text>

        {step === 'email' && (
          <View style={s.form}>
            <View style={s.inputWrap}>
              <Ionicons name="mail-outline" size={20} color="#888" style={s.icon} />
              <TextInput style={s.input} placeholder={t('auth.email')} placeholderTextColor="#888"
                value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
            </View>
            <TouchableOpacity style={[s.btn, loading && s.btnDisabled]} onPress={handleSendCode} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{t('auth.sendCode')}</Text>}
            </TouchableOpacity>
          </View>
        )}

        {step === 'code' && (
          <View style={s.form}>
            <View style={s.inputWrap}>
              <Ionicons name="keypad-outline" size={20} color="#888" style={s.icon} />
              <TextInput style={s.input} placeholder={t('auth.verificationCode')} placeholderTextColor="#888"
                value={code} onChangeText={setCode} keyboardType="number-pad" maxLength={6} />
            </View>
            <TouchableOpacity style={[s.btn, loading && s.btnDisabled]} onPress={handleVerifyCode} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{t('auth.verifyCode')}</Text>}
            </TouchableOpacity>
            <TouchableOpacity onPress={handleSendCode} style={s.resend}>
              <Text style={s.resendText}>{t('auth.resendCode')}</Text>
            </TouchableOpacity>
          </View>
        )}

        {step === 'password' && (
          <View style={s.form}>
            <View style={s.inputWrap}>
              <Ionicons name="lock-closed-outline" size={20} color="#888" style={s.icon} />
              <TextInput style={s.input} placeholder={t('auth.newPassword')} placeholderTextColor="#888"
                value={newPassword} onChangeText={setNewPassword} secureTextEntry />
            </View>
            <View style={s.inputWrap}>
              <Ionicons name="lock-closed-outline" size={20} color="#888" style={s.icon} />
              <TextInput style={s.input} placeholder={t('auth.confirmPassword')} placeholderTextColor="#888"
                value={confirmPassword} onChangeText={setConfirmPassword} secureTextEntry />
            </View>
            <TouchableOpacity style={[s.btn, loading && s.btnDisabled]} onPress={handleResetPassword} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{t('auth.resetPassword')}</Text>}
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  scroll: { flexGrow: 1, padding: 24, justifyContent: 'center' },
  backBtn: { position: 'absolute', top: 0, left: 0, padding: 8 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginTop: 16 },
  subtitle: { fontSize: 14, color: '#aaa', textAlign: 'center', marginTop: 8, marginBottom: 32, lineHeight: 20 },
  form: { gap: 16 },
  inputWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1e1e1e', borderRadius: 12, borderWidth: 1, borderColor: '#333', paddingHorizontal: 16, height: 52 },
  icon: { marginRight: 12 },
  input: { flex: 1, color: '#fff', fontSize: 16 },
  btn: { backgroundColor: '#4CAF50', borderRadius: 12, height: 52, justifyContent: 'center', alignItems: 'center' },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  resend: { alignItems: 'center', paddingTop: 8 },
  resendText: { color: '#4CAF50', fontSize: 14 },
});
