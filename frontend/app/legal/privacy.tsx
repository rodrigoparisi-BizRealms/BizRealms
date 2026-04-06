import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';
import { useTheme } from '../../context/ThemeContext';

const PRIVACY_CONTENT: Record<string, { updated: string; sections: { title: string; text: string }[] }> = {
  pt: {
    updated: 'Última atualização: Junho 2025',
    sections: [
      { title: '1. Informações que Coletamos', text: 'Coletamos informações fornecidas diretamente por você: nome, endereço de e-mail e dados opcionais de perfil (avatar, cidade). Também coletamos dados de jogabilidade (progresso, transações, rankings), dados do dispositivo (SO, idioma, fuso horário) e documento de identidade (quando necessário para saques via PayPal).' },
      { title: '2. Como Usamos Suas Informações', text: 'Usamos suas informações para: fornecer e melhorar a experiência do jogo; gerenciar sua conta; processar compras e recompensas no app; manter rankings; enviar notificações sobre eventos do jogo; e prevenir fraudes e abusos.' },
      { title: '3. Compartilhamento de Informações', text: 'Não vendemos suas informações pessoais. Podemos compartilhar dados limitados com: processadores de pagamento (para compras e recompensas via PayPal); provedores de análise (dados agregados e anonimizados); e autoridades legais (quando exigido por lei).' },
      { title: '4. Segurança dos Dados', text: 'Implementamos medidas de segurança padrão da indústria, incluindo criptografia, autenticação segura (JWT), autenticação biométrica opcional e auditorias regulares de segurança para proteger seus dados.' },
      { title: '5. Seus Direitos (LGPD)', text: 'De acordo com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018), você tem o direito de: acessar seus dados pessoais; corrigir dados incorretos; solicitar a exclusão de sua conta e dados associados; exportar seus dados; revogar consentimento; e optar por não receber comunicações de marketing. Para exercer esses direitos, use a função "Zerar Conta" no perfil ou entre em contato conosco.' },
      { title: '6. Armazenamento Local', text: 'O aplicativo utiliza armazenamento local para tokens de autenticação, preferências do usuário (tema, idioma, sons) e cache offline. Não utilizamos cookies de rastreamento de terceiros.' },
      { title: '7. Privacidade de Menores', text: 'O BizRealms não é destinado a menores de 13 anos (ou a idade mínima em sua jurisdição). Não coletamos intencionalmente dados de crianças. Se você acredita que coletamos dados de um menor, entre em contato imediatamente.' },
      { title: '8. Transferência Internacional de Dados', text: 'Seus dados podem ser processados em servidores localizados fora do seu país. Garantimos que as salvaguardas apropriadas estejam em vigor para transferências internacionais, conforme exigido pela LGPD.' },
      { title: '9. Retenção de Dados', text: 'Mantemos seus dados enquanto sua conta estiver ativa. Após a exclusão da conta, podemos reter dados anonimizados para fins de análise por até 90 dias.' },
      { title: '10. Anúncios e Monetização', text: 'O BizRealms pode exibir anúncios de parceiros publicitários. Os dados compartilhados com redes de anúncios são limitados a identificadores de dispositivo anonimizados e não incluem dados pessoais identificáveis. Uma parcela da receita de anúncios (5%) é distribuída aos jogadores com melhor ranking.' },
      { title: '11. Alterações nesta Política', text: 'Podemos atualizar esta política periodicamente. Notificaremos você sobre mudanças significativas através do aplicativo. O uso continuado após as alterações constitui aceitação da nova política.' },
      { title: '12. Contato e Encarregado (DPO)', text: 'Para questões relacionadas à privacidade ou para exercer seus direitos, entre em contato: privacy@bizrealms.com\n\nEncarregado de Proteção de Dados (DPO):\nE-mail: dpo@bizrealms.com' },
    ],
  },
  en: {
    updated: 'Last updated: June 2025',
    sections: [
      { title: '1. Information We Collect', text: 'We collect information you provide directly: name, email address, and optional profile data (avatar, city). We also collect gameplay data (progress, transactions, rankings), device information (OS, language, timezone), and identity documents (when required for PayPal withdrawals).' },
      { title: '2. How We Use Your Information', text: 'We use your information to: provide and improve the game experience; manage your account; process in-app purchases and rewards; maintain rankings; send notifications about game events; and prevent fraud and abuse.' },
      { title: '3. Information Sharing', text: 'We do not sell your personal information. We may share limited data with: payment processors (for purchases and rewards via PayPal); analytics providers (aggregated, anonymized data); and law enforcement (when required by law).' },
      { title: '4. Data Security', text: 'We implement industry-standard security measures including encryption, secure authentication (JWT), optional biometric authentication, and regular security audits to protect your data.' },
      { title: '5. Your Rights', text: 'You have the right to: access your personal data; correct inaccurate data; delete your account and associated data; export your data; revoke consent; and opt-out of marketing communications. Use the "Reset Account" feature in your profile or contact us.' },
      { title: '6. Local Storage', text: 'The App uses local storage for authentication tokens and user preferences (theme, language, sounds). We do not use third-party tracking cookies.' },
      { title: '7. Children\'s Privacy', text: 'BizRealms is not intended for children under 13 (or the minimum age in your jurisdiction). We do not knowingly collect data from children.' },
      { title: '8. International Data Transfers', text: 'Your data may be processed in servers located outside your country. We ensure appropriate safeguards are in place for international transfers.' },
      { title: '9. Data Retention', text: 'We retain your data for as long as your account is active. After account deletion, we may retain anonymized data for analytics purposes for up to 90 days.' },
      { title: '10. Ads & Monetization', text: 'BizRealms may display ads from advertising partners. Data shared with ad networks is limited to anonymized device identifiers and does not include personally identifiable information. A portion of ad revenue (5%) is distributed to top-ranked players.' },
      { title: '11. Changes to This Policy', text: 'We may update this policy from time to time. We will notify you of significant changes through the App.' },
      { title: '12. Contact Us', text: 'For privacy-related questions or to exercise your rights, contact us at: privacy@bizrealms.com' },
    ],
  },
};

export default function Privacy() {
  const router = useRouter();
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const content = PRIVACY_CONTENT[language] || PRIVACY_CONTENT['en'];

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={[s.header, { borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[s.title, { color: colors.text }]}>{t('legal.privacy') || 'Política de Privacidade'}</Text>
      </View>
      <ScrollView style={s.content} showsVerticalScrollIndicator={false}>
        <Text style={[s.updated, { color: colors.textSecondary }]}>{content.updated}</Text>

        {content.sections.map((section, idx) => (
          <React.Fragment key={idx}>
            <Text style={s.sectionTitle}>{section.title}</Text>
            <Text style={[s.text, { color: colors.textSecondary }]}>{section.text}</Text>
          </React.Fragment>
        ))}

        <View style={{ height: 60 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1 },
  back: { marginRight: 12, padding: 4 },
  title: { fontSize: 20, fontWeight: 'bold' },
  content: { flex: 1, padding: 20 },
  updated: { color: '#888', fontSize: 12, marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#4CAF50', marginTop: 20, marginBottom: 8 },
  text: { fontSize: 14, color: '#ccc', lineHeight: 22, marginBottom: 8 },
});
