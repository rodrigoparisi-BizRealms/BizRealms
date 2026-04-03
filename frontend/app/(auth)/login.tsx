import React, { useState, useEffect } from 'react';
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
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../../context/LanguageContext';
import axios from 'axios';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';

// Required for web-based auth sessions
WebBrowser.maybeCompleteAuthSession();

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// Google OAuth Config
const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID || '';
const GOOGLE_DISCOVERY = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  revocationEndpoint: 'https://oauth2.googleapis.com/revoke',
};

const showMsg = (title: string, msg: string) => {
  if (Platform.OS === 'web') window.alert(`${title}\n${msg}`);
  else Alert.alert(title, msg);
};

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState<string | null>(null);
  const { login } = useAuth();
  const router = useRouter();
  const { t } = useLanguage();

  // Google OAuth request
  const redirectUri = AuthSession.makeRedirectUri({ preferLocalhost: false });
  const [googleRequest, googleResponse, googlePromptAsync] = AuthSession.useAuthRequest(
    {
      clientId: GOOGLE_CLIENT_ID,
      scopes: ['openid', 'profile', 'email'],
      redirectUri,
      responseType: AuthSession.ResponseType.Token,
    },
    GOOGLE_DISCOVERY
  );

  // Handle Google OAuth response
  useEffect(() => {
    if (googleResponse?.type === 'success') {
      const { access_token } = googleResponse.params;
      if (access_token) {
        handleSocialAuth('google', access_token);
      }
    } else if (googleResponse?.type === 'error') {
      console.error('Google auth error:', googleResponse.error);
      setSocialLoading(null);
    } else if (googleResponse?.type === 'dismiss') {
      setSocialLoading(null);
    }
  }, [googleResponse]);

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
    if (!GOOGLE_CLIENT_ID) {
      showMsg(
        'Google Sign-In',
        'Configure EXPO_PUBLIC_GOOGLE_CLIENT_ID no .env para habilitar autenticação Google. Crie um projeto no Google Cloud Console > APIs & Services > Credentials > OAuth 2.0 Client IDs.'
      );
      return;
    }
    setSocialLoading('google');
    try {
      await googlePromptAsync();
    } catch (e: any) {
      console.error('Google prompt error:', e);
      showMsg(t('general.error'), 'Erro ao iniciar Google Sign-In');
      setSocialLoading(null);
    }
  };

  const handleAppleLogin = async () => {
    if (Platform.OS !== 'ios') {
      showMsg('Apple Sign-In', 'Apple Sign-In está disponível apenas em dispositivos iOS.');
      return;
    }
    setSocialLoading('apple');
    try {
      const AppleAuth = await import('expo-apple-authentication');
      const credential = await AppleAuth.signInAsync({
        requestedScopes: [
          AppleAuth.AppleAuthenticationScope.FULL_NAME,
          AppleAuth.AppleAuthenticationScope.EMAIL,
        ],
      });
      
      if (credential.identityToken) {
        const fullName = credential.fullName;
        const name = fullName ? `${fullName.givenName || ''} ${fullName.familyName || ''}`.trim() : undefined;
        await handleSocialAuth('apple', credential.identityToken, name, credential.email || undefined);
      } else {
        showMsg(t('general.error'), 'Não foi possível obter credenciais da Apple');
      }
    } catch (e: any) {
      if (e.code !== 'ERR_REQUEST_CANCELED') {
        console.error('Apple auth error:', e);
        showMsg(t('general.error'), 'Erro ao iniciar Apple Sign-In');
      }
    } finally {
      setSocialLoading(null);
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
          <TouchableOpacity
            style={[styles.socialBtn, socialLoading === 'google' && styles.buttonDisabled]}
            onPress={handleGoogleLogin}
            disabled={!!socialLoading || loading}
          >
            {socialLoading === 'google' ? (
              <ActivityIndicator size="small" color="#DB4437" />
            ) : (
              <Ionicons name="logo-google" size={22} color="#DB4437" />
            )}
            <Text style={styles.socialBtnText}>{t('auth.continueWithGoogle')}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.socialBtn, styles.appleBtn, socialLoading === 'apple' && styles.buttonDisabled]}
            onPress={handleAppleLogin}
            disabled={!!socialLoading || loading}
          >
            {socialLoading === 'apple' ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="logo-apple" size={22} color="#fff" />
            )}
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
