import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';

export default function Terms() {
  const router = useRouter();
  const { t } = useLanguage();

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>{t('legal.terms')}</Text>
      </View>
      <ScrollView style={s.content} showsVerticalScrollIndicator={false}>
        <Text style={s.updated}>Last updated: June 2025</Text>

        <Text style={s.sectionTitle}>1. Acceptance of Terms</Text>
        <Text style={s.text}>By downloading, installing, or using BizRealms ("the App"), you agree to be bound by these Terms of Use. If you do not agree, do not use the App.</Text>

        <Text style={s.sectionTitle}>2. Description of Service</Text>
        <Text style={s.text}>BizRealms is a business simulation game where players manage virtual companies, investments, jobs, and assets. The in-game currency and assets have no real-world monetary value unless explicitly stated in our rewards program.</Text>

        <Text style={s.sectionTitle}>3. Account Registration</Text>
        <Text style={s.text}>You must provide accurate information when creating an account. You are responsible for maintaining the security of your account credentials. One account per person is allowed.</Text>

        <Text style={s.sectionTitle}>4. In-App Purchases</Text>
        <Text style={s.text}>The App may offer in-app purchases. All purchases are final and non-refundable, except as required by applicable law. Virtual items purchased have no real-world value.</Text>

        <Text style={s.sectionTitle}>5. Real Money Rewards</Text>
        <Text style={s.text}>BizRealms may offer real money rewards to top-ranked players. Eligibility, amounts, and payment methods are determined by BizRealms at its sole discretion. Players must provide valid payment information (e.g., PIX key) to receive rewards.</Text>

        <Text style={s.sectionTitle}>6. Prohibited Conduct</Text>
        <Text style={s.text}>You may not: use cheats, exploits, or automation; create multiple accounts; harass other players; attempt to manipulate rankings; or reverse-engineer the App.</Text>

        <Text style={s.sectionTitle}>7. Intellectual Property</Text>
        <Text style={s.text}>All content, graphics, logos, and software in BizRealms are owned by BizRealms or its licensors and are protected by intellectual property laws.</Text>

        <Text style={s.sectionTitle}>8. Termination</Text>
        <Text style={s.text}>We may suspend or terminate your account at any time for violation of these terms or for any other reason at our discretion.</Text>

        <Text style={s.sectionTitle}>9. Limitation of Liability</Text>
        <Text style={s.text}>BizRealms is provided "as is" without warranties. We are not liable for any indirect, incidental, or consequential damages arising from your use of the App.</Text>

        <Text style={s.sectionTitle}>10. Changes to Terms</Text>
        <Text style={s.text}>We may update these terms at any time. Continued use of the App after changes constitutes acceptance of the new terms.</Text>

        <Text style={s.sectionTitle}>11. Contact</Text>
        <Text style={s.text}>For questions about these Terms, contact us at: support@bizrealms.com</Text>

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
