# Instruções para Configurar GitHub Pages - BizRealms

## PASSO 1: Adicionar os arquivos que faltam na pasta `docs`

Você precisa adicionar **3 arquivos novos** na pasta `docs` do repositório.

### Arquivo 1: `docs/.nojekyll`
1. Vá para: https://github.com/rodrigoparisi-BizRealms/BizRealms/tree/main/docs
2. Clique em **"Add file"** > **"Create new file"**
3. No campo do nome, digite: `.nojekyll`
4. Deixe o conteúdo **VAZIO** (não escreva nada)
5. Clique em **"Commit changes"**

### Arquivo 2: `docs/index.html`
1. Volte para: https://github.com/rodrigoparisi-BizRealms/BizRealms/tree/main/docs
2. Clique em **"Add file"** > **"Create new file"**
3. No campo do nome, digite: `index.html`
4. Cole o conteúdo do BLOCO A (abaixo)
5. Clique em **"Commit changes"**

### Arquivo 3: `docs/privacy-policy.html`
1. Volte para: https://github.com/rodrigoparisi-BizRealms/BizRealms/tree/main/docs
2. Clique em **"Add file"** > **"Create new file"**
3. No campo do nome, digite: `privacy-policy.html`
4. Cole o conteúdo do BLOCO B (abaixo)
5. Clique em **"Commit changes"**

### Arquivo 4 (ATUALIZAR): `docs/delete-account.html`
1. Vá para: https://github.com/rodrigoparisi-BizRealms/BizRealms/blob/main/docs/delete-account.html
2. Clique no ícone de **lápis (editar)**
3. **Selecione TUDO** (Ctrl+A) e **APAGUE**
4. Cole o conteúdo do BLOCO C (abaixo)
5. Clique em **"Commit changes"**

---

## PASSO 2: Ativar GitHub Pages

1. Vá para: https://github.com/rodrigoparisi-BizRealms/BizRealms/settings/pages
2. Em **"Source"**, selecione: **"Deploy from a branch"**
3. Em **"Branch"**, selecione: **main**
4. Na pasta ao lado, selecione: **/docs**
5. Clique em **"Save"**
6. Aguarde ~2 minutos para o deploy

---

## PASSO 3: Testar as URLs

Após configurar, suas URLs serão:
- **Exclusão de Conta:** https://rodrigoparisi-bizrealms.github.io/BizRealms/delete-account.html
- **Política de Privacidade:** https://rodrigoparisi-bizrealms.github.io/BizRealms/privacy-policy.html

---

## PASSO 4: Usar na Google Play Console

Cole essas URLs nos campos obrigatórios:
- **Privacy Policy URL:** https://rodrigoparisi-bizrealms.github.io/BizRealms/privacy-policy.html
- **Account Deletion URL:** https://rodrigoparisi-bizrealms.github.io/BizRealms/delete-account.html
