import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';

export default function Privacy() {
  const router = useRouter();
  const { t } = useLanguage();

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>{t('legal.privacy')}</Text>
      </View>
      <ScrollView style={s.content} showsVerticalScrollIndicator={false}>
        <Text style={s.updated}>Last updated: June 2025</Text>

        <Text style={s.sectionTitle}>1. Information We Collect</Text>
        <Text style={s.text}>We collect information you provide directly: name, email address, and optional profile data (avatar, city). We also collect gameplay data (progress, transactions, rankings) and device information (OS, language, timezone).</Text>

        <Text style={s.sectionTitle}>2. How We Use Your Information</Text>
        <Text style={s.text}>We use your information to: provide and improve the game experience; manage your account; process in-app purchases and rewards; maintain rankings; send notifications about game events; and prevent fraud and abuse.</Text>

        <Text style={s.sectionTitle}>3. Information Sharing</Text>
        <Text style={s.text}>We do not sell your personal information. We may share limited data with: payment processors (for purchases and rewards); analytics providers (aggregated, anonymized data); and law enforcement (when required by law).</Text>

        <Text style={s.sectionTitle}>4. Data Security</Text>
        <Text style={s.text}>We implement industry-standard security measures including encryption, secure authentication (JWT), and regular security audits to protect your data.</Text>

        <Text style={s.sectionTitle}>5. Your Rights</Text>
        <Text style={s.text}>You have the right to: access your personal data; correct inaccurate data; delete your account and associated data; export your data; and opt-out of marketing communications.</Text>

        <Text style={s.sectionTitle}>6. Cookies & Tracking</Text>
        <Text style={s.text}>The App uses local storage for authentication tokens and user preferences. We do not use third-party tracking cookies.</Text>

        <Text style={s.sectionTitle}>7. Children's Privacy</Text>
        <Text style={s.text}>BizRealms is not intended for children under 13 (or the minimum age in your jurisdiction). We do not knowingly collect data from children.</Text>

        <Text style={s.sectionTitle}>8. International Data Transfers</Text>
        <Text style={s.text}>Your data may be processed in servers located outside your country. We ensure appropriate safeguards are in place for international transfers.</Text>

        <Text style={s.sectionTitle}>9. Data Retention</Text>
        <Text style={s.text}>We retain your data for as long as your account is active. After account deletion, we may retain anonymized data for analytics purposes.</Text>

        <Text style={s.sectionTitle}>10. Changes to This Policy</Text>
        <Text style={s.text}>We may update this policy from time to time. We will notify you of significant changes through the App.</Text>

        <Text style={s.sectionTitle}>11. Contact Us</Text>
        <Text style={s.text}>For privacy-related questions or to exercise your rights, contact us at: privacy@bizrealms.com</Text>

        <View style={{ height: 60 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#222' },
  back: { marginRight: 12, padding: 4 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  content: { flex: 1, padding: 20 },
  updated: { color: '#888', fontSize: 12, marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#4CAF50', marginTop: 20, marginBottom: 8 },
  text: { fontSize: 14, color: '#ccc', lineHeight: 22, marginBottom: 8 },
});
