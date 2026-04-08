# 🚀 GUIA COMPLETO: Publicar BizRealms nas Lojas
## Google Play Store + Apple App Store

---

## FASE 1: CRIAR CONTAS (Faça antes de tudo)

### 1.1 — Criar conta Expo (EAS) — GRATUITO
1. Acesse: https://expo.dev/signup
2. Crie sua conta (email + senha)
3. Após login, clique em **"Create a project"**
4. Nome do projeto: `bizrealms`
5. Anote o **Project ID** que aparece (formato: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
6. **ME ENVIE ESSE PROJECT ID** para eu configurar no app

### 1.2 — Criar conta Google Play Console — $25 (taxa única)
1. Acesse: https://play.google.com/console/signup
2. Faça login com sua conta Google
3. Pague a taxa de $25 (cartão de crédito/débito)
4. Preencha os dados da conta de desenvolvedor
5. Aguarde aprovação (geralmente 24-48h)

### 1.3 — Criar conta Apple Developer — $99/ano
1. Acesse: https://developer.apple.com/programs/enroll/
2. Faça login com seu Apple ID (ou crie um em https://appleid.apple.com)
3. Pague a assinatura anual de $99
4. Aguarde aprovação (pode levar 24-48h)
5. Após aprovação, anote:
   - **Apple ID** (seu email)
   - **Team ID** (em https://developer.apple.com/account → Membership)

---

## FASE 2: INSTALAR FERRAMENTAS NO SEU COMPUTADOR

### 2.1 — Instalar Node.js
- Baixe em: https://nodejs.org (versão LTS)
- Após instalar, abra o terminal e verifique:
```bash
node --version   # deve mostrar v18+ ou v20+
npm --version    # deve mostrar 9+
```

### 2.2 — Instalar EAS CLI
```bash
npm install -g eas-cli
```

### 2.3 — Fazer login no EAS
```bash
eas login
# Digite seu email e senha da conta Expo criada na Fase 1.1
```

### 2.4 — Instalar Git (se não tiver)
- Windows: https://git-scm.com/download/win
- Mac: `xcode-select --install`
- Linux: `sudo apt install git`

---

## FASE 3: BAIXAR O CÓDIGO DO PROJETO

### 3.1 — Baixar o código
Use a opção de **download/export** do Emergent para baixar o projeto completo.
Ou use o push para GitHub e clone no seu computador.

### 3.2 — Instalar dependências
```bash
cd frontend
npm install
# ou
yarn install
```

---

## FASE 4: BUILD ANDROID (APK + AAB)

### 4.1 — Build APK (para testar no celular)
```bash
cd frontend
eas build --platform android --profile preview
```
- Isso gera um arquivo `.apk` que você pode instalar direto no celular Android
- O build demora ~10-20 minutos na nuvem do EAS
- Ao terminar, você recebe um link para baixar o APK

### 4.2 — Build AAB (para Google Play Store)
```bash
eas build --platform android --profile production
```
- Gera um `.aab` (Android App Bundle) otimizado para a Play Store
- Este é o formato exigido pelo Google Play

### 4.3 — Testar o APK
1. Baixe o APK pelo link que o EAS fornece
2. Transfira para seu celular Android (WhatsApp, email, Google Drive)
3. Abra no celular e instale (pode pedir para "permitir instalação de fontes desconhecidas")
4. Teste TUDO: login, empresas, investimentos, boost com anúncio, player de música, etc.

---

## FASE 5: BUILD iOS

### 5.1 — Configurar credenciais iOS
```bash
eas credentials --platform ios
```
- O EAS vai guiar você para criar os certificados automaticamente
- Você precisa da sua Apple Developer Account configurada

### 5.2 — Build iOS
```bash
eas build --platform ios --profile production
```
- Gera um `.ipa` para a App Store
- Build demora ~15-30 minutos

---

## FASE 6: PUBLICAR NA GOOGLE PLAY STORE

### 6.1 — Preparar a ficha do app
1. Acesse: https://play.google.com/console
2. Clique em **"Criar app"**
3. Preencha:
   - Nome: **BizRealms**
   - Idioma padrão: **Português (Brasil)**
   - Tipo: **Jogo**
   - Gratuito
4. Preencha as seções obrigatórias:
   - **Ficha da loja**: descrição, screenshots, ícone
   - **Classificação do conteúdo**: responda o questionário IARC
   - **Política de privacidade**: URL da sua política (obrigatório)
   - **Público-alvo e conteúdo**: idade 13+

### 6.2 — Screenshots necessários (mínimo)
- **Celular**: 2 screenshots (1080x1920 ou similar)
- **Tablet 7"**: 1 screenshot (opcional mas recomendado)
- **Tablet 10"**: 1 screenshot (opcional)

### 6.3 — Upload do AAB
1. Vá em **Teste** → **Teste interno** (recomendado para começar)
2. Clique em **"Criar nova versão"**
3. Faça upload do arquivo `.aab` gerado na Fase 4.2
4. Adicione notas da versão: "Versão inicial do BizRealms"
5. Revise e publique

### 6.4 — Promover para Produção
1. Após testar no Teste Interno, vá em **Produção**
2. Promova a versão testada
3. Envie para revisão do Google (geralmente 1-3 dias)

---

## FASE 7: PUBLICAR NA APPLE APP STORE

### 7.1 — Acessar App Store Connect
1. Acesse: https://appstoreconnect.apple.com
2. Clique em **"My Apps"** → **"+"** → **"New App"**
3. Preencha:
   - Nome: **BizRealms**
   - Idioma: **Portuguese**
   - Bundle ID: `com.bizrealms.game`
   - SKU: `bizrealms-game`

### 7.2 — Preencher informações
- Descrição do app
- Screenshots (iPhone 6.7", iPhone 6.1", iPad)
- Categoria: Games → Simulation
- Classificação etária
- Política de privacidade (URL)

### 7.3 — Enviar o build via EAS
```bash
eas submit --platform ios --profile production
```
- O EAS envia automaticamente para o App Store Connect
- Você precisa fornecer seu Apple ID e App-specific password

### 7.4 — Submeter para revisão
1. No App Store Connect, selecione o build enviado
2. Preencha as informações de revisão
3. Submeta para revisão da Apple (geralmente 1-3 dias)

---

## FASE 8: PÓS-PUBLICAÇÃO

### 8.1 — Monitoramento
- **Google Play Console**: Veja downloads, crashes, avaliações
- **App Store Connect**: Veja downloads, crashes, avaliações
- **AdMob**: Monitore receita de anúncios em https://admob.google.com
- **Sentry**: Monitore erros em https://sentry.io
- **Railway**: Monitore o backend em https://railway.app

### 8.2 — Atualizações futuras
Para publicar atualizações:
```bash
# Incremente a versão no app.json (ex: 1.0.0 → 1.1.0)
# Depois:
eas build --platform android --profile production
eas build --platform ios --profile production

# Enviar para as lojas:
eas submit --platform android
eas submit --platform ios
```

---

## 📋 CHECKLIST RESUMIDO

- [ ] Conta Expo (EAS) criada
- [ ] Project ID configurado no app.json
- [ ] EAS CLI instalado no seu computador
- [ ] Login no EAS feito
- [ ] Código baixado e dependências instaladas
- [ ] Build APK de teste gerado e testado
- [ ] Conta Google Play Console criada ($25)
- [ ] Build AAB de produção gerado
- [ ] App publicado na Google Play
- [ ] Conta Apple Developer criada ($99/ano)
- [ ] Build iOS gerado
- [ ] App publicado na App Store
- [ ] AdMob gerando receita
- [ ] Política de privacidade publicada

---

## ⚠️ NOTAS IMPORTANTES

1. **Política de Privacidade**: Obrigatória para ambas as lojas. Você precisa criar uma página web com sua política. Ferramentas gratuitas: https://app-privacy-policy-generator.firebaseapp.com

2. **Ícones e Screenshots**: Já temos ícones configurados no projeto. Para screenshots, tire do seu celular após instalar o APK de teste.

3. **AdMob**: Os anúncios só aparecerão no build nativo (APK/AAB/IPA), não no preview web.

4. **Backend Railway**: Já está online em `https://bizrealms-production-ead0.up.railway.app`. Certifique-se que continua rodando.

5. **Custos totais**:
   - Google Play: $25 (uma vez)
   - Apple Developer: $99/ano
   - EAS Build: Gratuito (até 30 builds/mês no plano free)
   - Railway: Depende do uso (tem plano gratuito limitado)
