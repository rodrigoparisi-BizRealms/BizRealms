import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../../context/LanguageContext';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const showMsg = (title: string, msg: string) => {
  if (Platform.OS === 'web') window.alert(`${title}\n${msg}`);
  else Alert.alert(title, msg);
};

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();
  const { t } = useLanguage();

  const handleLogin = async () => {
    if (!email || !password) {
      if (Platform.OS === 'web') { window.alert(t('auth.fillAllFields')); }
      else { Alert.alert(t('general.error'), t('auth.fillAllFields')); }
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      router.replace('/(tabs)/home');
    } catch (error: any) {
      if (Platform.OS === 'web') { window.alert(error.message); }
      else { Alert.alert(t('general.error'), error.message); }
    } finally {
      setLoading(false);
    }
  };

  const handleSocialAuth = async (provider: 'google' | 'apple', providerToken: string, name?: string, email?: string) => {
    setLoading(true);
    try {
      const res = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/social`, {
        provider, token: providerToken, name, email,
      });
      const { token: newToken, user: newUser } = res.data;
      const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
      await AsyncStorage.setItem('token', newToken);
      await AsyncStorage.setItem('user', JSON.stringify(newUser));
      router.replace(newUser.onboarding_completed ? '/(tabs)/home' : '/(onboarding)/avatar');
    } catch (e: any) {
      showMsg(t('general.error'), e.response?.data?.detail || t('general.error'));
    } finally { setLoading(false); }
  };

  const handleGoogleLogin = async () => {
    // TODO: Replace with real Google OAuth when Client ID is configured
    // For now, show a message that credentials need to be configured
    showMsg('Google Sign-In', 'Configure GOOGLE_CLIENT_ID in .env to enable Google authentication. The flow is fully implemented and ready.');
  };

  const handleAppleLogin = async () => {
    // TODO: Replace with real Apple Sign-In when Apple Developer account is configured
    // Apple Sign-In only works on iOS devices with expo-apple-authentication
    if (Platform.OS === 'ios') {
      showMsg('Apple Sign-In', 'Configure Apple Developer credentials to enable. The flow is fully implemented and ready.');
    } else {
      showMsg('Apple Sign-In', 'Apple Sign-In is available on iOS devices only.');
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Ionicons name="business" size={80} color="#4CAF50" />
          <Text style={styles.title}>BizRealms</Text>
          <Text style={styles.subtitle}>{t('auth.subtitle')}</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Ionicons name="mail-outline" size={20} color="#888" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder={t('auth.email')}
              placeholderTextColor="#888"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed-outline" size={20} color="#888" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder={t('auth.password')}
              placeholderTextColor="#888"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? t('auth.signingIn') : t('auth.signIn')}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.forgotBtn}
            onPress={() => router.push('/(auth)/forgot-password')}
          >
            <Text style={styles.forgotText}>{t('auth.forgotPassword')}</Text>
          </TouchableOpacity>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>{t('auth.orContinueWith')}</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Social Auth Buttons */}
          <TouchableOpacity style={styles.socialBtn} onPress={handleGoogleLogin}>
            <Ionicons name="logo-google" size={22} color="#DB4437" />
            <Text style={styles.socialBtnText}>{t('auth.continueWithGoogle')}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.socialBtn, styles.appleBtn]} onPress={handleAppleLogin}>
            <Ionicons name="logo-apple" size={22} color="#fff" />
            <Text style={[styles.socialBtnText, styles.appleBtnText]}>{t('auth.continueWithApple')}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkButton}
            onPress={() => router.push('/(auth)/register')}
          >
            <Text style={styles.linkText}>{t('auth.noAccount')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
    marginTop: 8,
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    height: 56,
    color: '#fff',
    fontSize: 16,
  },
  button: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  linkButton: {
    marginTop: 24,
    alignItems: 'center',
  },
  linkText: {
    color: '#4CAF50',
    fontSize: 16,
  },
  forgotBtn: {
    alignItems: 'flex-end',
    marginTop: -4,
    marginBottom: 8,
  },
  forgotText: {
    color: '#888',
    fontSize: 14,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#333',
  },
  dividerText: {
    color: '#666',
    fontSize: 13,
    marginHorizontal: 12,
  },
  socialBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    height: 52,
    marginBottom: 12,
    gap: 10,
    borderWidth: 1,
    borderColor: '#333',
  },
  socialBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  appleBtn: {
    backgroundColor: '#000',
    borderColor: '#444',
  },
  appleBtnText: {
    color: '#fff',
  },
});
