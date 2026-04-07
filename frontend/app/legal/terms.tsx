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
      { title: '4. Compras no Aplicativo (Pagamentos do Jogador ao BizRealms)', text: 'O Aplicativo pode oferecer compras no app processadas via Apple App Store, Google Play Store ou Stripe. Todas as compras são finais e não reembolsáveis, exceto conforme exigido pela legislação aplicável. Itens virtuais comprados (moedas, perks, cosméticos) não possuem valor no mundo real e não podem ser transferidos, vendidos ou trocados fora do Aplicativo. Cobranças são processadas pela plataforma correspondente (Apple/Google/Stripe) e sujeitas às políticas de reembolso das respectivas plataformas. O BizRealms reserva-se o direito de modificar preços, ofertas e itens disponíveis para compra a qualquer momento.' },
      { title: '5. Recompensas em Dinheiro Real (Pagamentos do BizRealms ao Jogador)', text: 'O BizRealms pode oferecer recompensas em dinheiro real para jogadores com melhor ranking no jogo. As regras são:\n\n• ELEGIBILIDADE: Apenas jogadores que estejam entre os primeiros colocados no ranking semanal ou mensal são elegíveis. O BizRealms determina os critérios de elegibilidade a seu exclusivo critério.\n\n• VALORES: Os valores das recompensas são definidos pelo BizRealms e podem ser alterados a qualquer momento. Os valores são divulgados na seção "Prize Pool" do ranking do jogo.\n\n• FORMA DE PAGAMENTO: Todas as recompensas em dinheiro real são pagas exclusivamente via PayPal. O jogador deve cadastrar um endereço de e-mail PayPal válido e verificado em seu perfil, além de fornecer Nome Completo e Documento de Identidade para fins de verificação.\n\n• PRAZO DE PAGAMENTO: Os pagamentos são processados em até 15 dias úteis após o encerramento do período de ranking. O BizRealms não se responsabiliza por atrasos causados pelo PayPal ou pelo jogador fornecer dados incorretos.\n\n• IMPOSTOS: O jogador é inteiramente responsável por declarar e pagar quaisquer impostos aplicáveis sobre as recompensas recebidas, conforme a legislação de seu país de residência.\n\n• LIMITES: O BizRealms reserva-se o direito de limitar, suspender ou cancelar o programa de recompensas a qualquer momento, sem aviso prévio.' },
      { title: '6. Verificação de Identidade', text: 'Para receber recompensas em dinheiro real, o jogador deve fornecer: Nome completo (conforme documento oficial), Documento de identidade válido (CPF, RG, Passaporte ou equivalente), e E-mail PayPal verificado. O BizRealms pode solicitar documentação adicional para fins de verificação e prevenção de fraudes. Informações falsas resultarão em banimento permanente e perda de recompensas pendentes.' },
      { title: '7. Conduta Proibida', text: 'Você não pode: usar trapaças, exploits ou automação; criar múltiplas contas; assediar outros jogadores; tentar manipular rankings; fazer engenharia reversa do Aplicativo; utilizar contas PayPal de terceiros para receber recompensas; ou compartilhar credenciais de acesso.' },
      { title: '8. Propriedade Intelectual', text: 'Todo conteúdo, gráficos, logos e software do BizRealms são de propriedade do BizRealms ou seus licenciadores e são protegidos por leis de propriedade intelectual.' },
      { title: '9. Anúncios', text: 'O Aplicativo pode exibir anúncios como parte do modelo de monetização. Os jogadores podem optar por assistir anúncios para obter benefícios no jogo (como multiplicar receita de empresas em 10x por 3 horas). A exibição de anúncios está sujeita à disponibilidade da rede de anúncios.' },
      { title: '10. Rescisão', text: 'Podemos suspender ou encerrar sua conta a qualquer momento por violação destes termos ou por qualquer outro motivo a nosso critério. Em caso de encerramento: compras no app não serão reembolsadas, recompensas pendentes serão canceladas, e dados pessoais serão tratados conforme nossa Política de Privacidade.' },
      { title: '11. Isenção de Garantias e Limitação de Responsabilidade', text: 'O BizRealms é fornecido "como está" sem garantias de qualquer tipo, expressas ou implícitas. Não somos responsáveis por: interrupções de serviço, perda de dados do jogo, falhas em pagamentos do PayPal, danos indiretos ou consequenciais, ou variações nos valores de recompensas. A responsabilidade máxima do BizRealms será limitada ao valor efetivamente pago pelo jogador em compras no app nos últimos 12 meses.' },
      { title: '12. Lei Aplicável e Foro', text: 'Estes Termos são regidos pelas leis da República Federativa do Brasil. Quaisquer disputas serão resolvidas no foro da comarca do desenvolvedor, com aplicação do Código de Defesa do Consumidor quando aplicável.' },
      { title: '13. Alterações nos Termos', text: 'Podemos atualizar estes termos a qualquer momento. Alterações significativas serão notificadas dentro do Aplicativo. O uso continuado do Aplicativo após as alterações constitui aceitação dos novos termos.' },
      { title: '14. Contato', text: 'Para questões sobre estes Termos, entre em contato: support@bizrealms.com' },
    ],
  },
  en: {
    updated: 'Last updated: June 2025',
    sections: [
      { title: '1. Acceptance of Terms', text: 'By downloading, installing, or using BizRealms ("the App"), you agree to be bound by these Terms of Use. If you do not agree, do not use the App.' },
      { title: '2. Description of Service', text: 'BizRealms is a business simulation game where players manage virtual companies, investments, jobs, and assets. The in-game currency and assets have no real-world monetary value unless explicitly stated in our rewards program.' },
      { title: '3. Account Registration', text: 'You must provide accurate information when creating an account. You are responsible for maintaining the security of your account credentials. One account per person is allowed.' },
      { title: '4. In-App Purchases (Player Payments to BizRealms)', text: 'The App may offer in-app purchases processed via Apple App Store, Google Play Store, or Stripe. All purchases are final and non-refundable, except as required by applicable law. Virtual items purchased (coins, perks, cosmetics) have no real-world value and cannot be transferred, sold, or exchanged outside the App. Charges are processed by the corresponding platform (Apple/Google/Stripe) and are subject to the refund policies of the respective platforms. BizRealms reserves the right to modify prices, offers, and items available for purchase at any time.' },
      { title: '5. Real Money Rewards (BizRealms Payments to Players)', text: 'BizRealms may offer real money rewards to top-ranked players. The rules are:\n\n• ELIGIBILITY: Only players who rank among the top positions in the weekly or monthly ranking are eligible. BizRealms determines eligibility criteria at its sole discretion.\n\n• AMOUNTS: Reward amounts are determined by BizRealms and may be changed at any time. Amounts are displayed in the "Prize Pool" section of the game rankings.\n\n• PAYMENT METHOD: All real money rewards are paid exclusively via PayPal. Players must register a valid and verified PayPal email address in their profile, along with their Full Name and Identity Document for verification purposes.\n\n• PAYMENT TIMELINE: Payments are processed within 15 business days after the ranking period ends. BizRealms is not responsible for delays caused by PayPal or by incorrect player information.\n\n• TAXES: Players are solely responsible for declaring and paying any applicable taxes on rewards received, according to the laws of their country of residence.\n\n• LIMITS: BizRealms reserves the right to limit, suspend, or cancel the rewards program at any time without prior notice.' },
      { title: '6. Identity Verification', text: 'To receive real money rewards, players must provide: Full legal name (as shown on official documents), valid identity document (passport, national ID, or equivalent), and a verified PayPal email. BizRealms may request additional documentation for verification and fraud prevention. False information will result in permanent ban and forfeiture of pending rewards.' },
      { title: '7. Prohibited Conduct', text: 'You may not: use cheats, exploits, or automation; create multiple accounts; harass other players; attempt to manipulate rankings; reverse-engineer the App; use third-party PayPal accounts to receive rewards; or share login credentials.' },
      { title: '8. Intellectual Property', text: 'All content, graphics, logos, and software in BizRealms are owned by BizRealms or its licensors and are protected by intellectual property laws.' },
      { title: '9. Advertisements', text: 'The App may display advertisements as part of the monetization model. Players may opt to watch ads for in-game benefits (such as multiplying company revenue by 10x for 3 hours). Ad display is subject to ad network availability.' },
      { title: '10. Termination', text: 'We may suspend or terminate your account at any time for violation of these terms or for any other reason at our discretion. Upon termination: in-app purchases will not be refunded, pending rewards will be cancelled, and personal data will be handled according to our Privacy Policy.' },
      { title: '11. Disclaimers and Limitation of Liability', text: 'BizRealms is provided "as is" without warranties of any kind, express or implied. We are not liable for: service interruptions, loss of game data, PayPal payment failures, indirect or consequential damages, or variations in reward amounts. Maximum liability of BizRealms shall be limited to the amount actually paid by the player in in-app purchases in the last 12 months.' },
      { title: '12. Governing Law', text: 'These Terms are governed by the laws of the Federative Republic of Brazil. Any disputes shall be resolved in the courts of the developer\'s jurisdiction.' },
      { title: '13. Changes to Terms', text: 'We may update these terms at any time. Significant changes will be notified within the App. Continued use of the App after changes constitutes acceptance of the new terms.' },
      { title: '14. Contact', text: 'For questions about these Terms, contact us at: support@bizrealms.com' },
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
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1 },
  back: { marginRight: 12, padding: 4 },
  title: { fontSize: 20, fontWeight: 'bold' },
  content: { flex: 1, padding: 20 },
  updated: { color: '#888', fontSize: 12, marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#4CAF50', marginTop: 20, marginBottom: 8 },
  text: { fontSize: 14, color: '#ccc', lineHeight: 22, marginBottom: 8 },
});
