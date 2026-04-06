import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';
import { useTheme } from '../../context/ThemeContext';

const TERMS_CONTENT: Record<string, { updated: string; sections: { title: string; text: string }[] }> = {
  pt: {
    updated: 'Última atualização: Junho 2025',
    sections: [
      { title: '1. Aceitação dos Termos', text: 'Ao baixar, instalar ou usar o BizRealms ("o Aplicativo"), você concorda em ficar vinculado a estes Termos de Uso. Se você não concordar, não use o Aplicativo.' },
      { title: '2. Descrição do Serviço', text: 'BizRealms é um jogo de simulação de negócios onde os jogadores gerenciam empresas virtuais, investimentos, empregos e ativos. A moeda e os ativos do jogo não possuem valor monetário real, exceto quando explicitamente declarado em nosso programa de recompensas.' },
      { title: '3. Registro de Conta', text: 'Você deve fornecer informações precisas ao criar uma conta. Você é responsável por manter a segurança de suas credenciais. É permitida apenas uma conta por pessoa.' },
      { title: '4. Compras no Aplicativo', text: 'O Aplicativo pode oferecer compras no app. Todas as compras são finais e não reembolsáveis, exceto conforme exigido pela legislação aplicável. Itens virtuais comprados não possuem valor no mundo real.' },
      { title: '5. Recompensas em Dinheiro Real', text: 'O BizRealms pode oferecer recompensas em dinheiro real para jogadores com melhor ranking. Elegibilidade, valores e métodos de pagamento são determinados pelo BizRealms a seu exclusivo critério. Os jogadores devem fornecer informações válidas de pagamento (ex: conta PayPal e documento de identidade) para receber recompensas.' },
      { title: '6. Conduta Proibida', text: 'Você não pode: usar trapaças, exploits ou automação; criar múltiplas contas; assediar outros jogadores; tentar manipular rankings; ou fazer engenharia reversa do Aplicativo.' },
      { title: '7. Propriedade Intelectual', text: 'Todo conteúdo, gráficos, logos e software do BizRealms são de propriedade do BizRealms ou seus licenciadores e são protegidos por leis de propriedade intelectual.' },
      { title: '8. Anúncios', text: 'O Aplicativo pode exibir anúncios como parte do modelo de monetização. Os jogadores podem optar por assistir anúncios para obter benefícios no jogo (como duplicar recompensas ou desbloquear ofertas). A exibição de anúncios está sujeita à disponibilidade da rede de anúncios.' },
      { title: '9. Rescisão', text: 'Podemos suspender ou encerrar sua conta a qualquer momento por violação destes termos ou por qualquer outro motivo a nosso critério.' },
      { title: '10. Limitação de Responsabilidade', text: 'O BizRealms é fornecido "como está" sem garantias. Não somos responsáveis por danos indiretos, incidentais ou consequenciais decorrentes do uso do Aplicativo.' },
      { title: '11. Lei Aplicável', text: 'Estes Termos são regidos pelas leis da República Federativa do Brasil. Quaisquer disputas serão resolvidas no foro da comarca do desenvolvedor.' },
      { title: '12. Alterações nos Termos', text: 'Podemos atualizar estes termos a qualquer momento. O uso continuado do Aplicativo após as alterações constitui aceitação dos novos termos.' },
      { title: '13. Contato', text: 'Para questões sobre estes Termos, entre em contato: support@bizrealms.com' },
    ],
  },
  en: {
    updated: 'Last updated: June 2025',
    sections: [
      { title: '1. Acceptance of Terms', text: 'By downloading, installing, or using BizRealms ("the App"), you agree to be bound by these Terms of Use. If you do not agree, do not use the App.' },
      { title: '2. Description of Service', text: 'BizRealms is a business simulation game where players manage virtual companies, investments, jobs, and assets. The in-game currency and assets have no real-world monetary value unless explicitly stated in our rewards program.' },
      { title: '3. Account Registration', text: 'You must provide accurate information when creating an account. You are responsible for maintaining the security of your account credentials. One account per person is allowed.' },
      { title: '4. In-App Purchases', text: 'The App may offer in-app purchases. All purchases are final and non-refundable, except as required by applicable law. Virtual items purchased have no real-world value.' },
      { title: '5. Real Money Rewards', text: 'BizRealms may offer real money rewards to top-ranked players. Eligibility, amounts, and payment methods are determined by BizRealms at its sole discretion. Players must provide valid payment information (e.g., PayPal account and identity document) to receive rewards.' },
      { title: '6. Prohibited Conduct', text: 'You may not: use cheats, exploits, or automation; create multiple accounts; harass other players; attempt to manipulate rankings; or reverse-engineer the App.' },
      { title: '7. Intellectual Property', text: 'All content, graphics, logos, and software in BizRealms are owned by BizRealms or its licensors and are protected by intellectual property laws.' },
      { title: '8. Advertisements', text: 'The App may display advertisements as part of the monetization model. Players may opt to watch ads for in-game benefits (such as doubling rewards or unlocking offers). Ad display is subject to ad network availability.' },
      { title: '9. Termination', text: 'We may suspend or terminate your account at any time for violation of these terms or for any other reason at our discretion.' },
      { title: '10. Limitation of Liability', text: 'BizRealms is provided "as is" without warranties. We are not liable for any indirect, incidental, or consequential damages arising from your use of the App.' },
      { title: '11. Changes to Terms', text: 'We may update these terms at any time. Continued use of the App after changes constitutes acceptance of the new terms.' },
      { title: '12. Contact', text: 'For questions about these Terms, contact us at: support@bizrealms.com' },
    ],
  },
};

export default function Terms() {
  const router = useRouter();
  const { t, language } = useLanguage();
  const { colors } = useTheme();
  const content = TERMS_CONTENT[language] || TERMS_CONTENT['en'];

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      <View style={[s.header, { borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[s.title, { color: colors.text }]}>{t('legal.terms') || 'Termos de Uso'}</Text>
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
  container: { flex: 1, backgroundColor: '#121212' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#222' },
  back: { marginRight: 12, padding: 4 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  content: { flex: 1, padding: 20 },
  updated: { color: '#888', fontSize: 12, marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#4CAF50', marginTop: 20, marginBottom: 8 },
  text: { fontSize: 14, color: '#ccc', lineHeight: 22, marginBottom: 8 },
});
