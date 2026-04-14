"""BizRealms - Main Server (Modularized)"""
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
import time as time_module

# Shared modules
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_DAYS, APPLE_BUNDLE_ID
from database import db, client

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ==================== APP SETUP ====================
app = FastAPI(title="BizRealms API")
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== RATE LIMITING ====================
class RateLimiter:
    """Simple in-memory rate limiter per IP and per user."""
    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_limited(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        now = time_module.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]
        if len(self.requests[key]) >= max_requests:
            return True
        self.requests[key].append(now)
        return False

rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    path = request.url.path
    if path.startswith("/api/auth/"):
        if rate_limiter.is_limited(f"auth:{client_ip}", max_requests=10, window_seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again later."})
    elif request.method == "POST":
        if rate_limiter.is_limited(f"post:{client_ip}", max_requests=30, window_seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})
    else:
        if rate_limiter.is_limited(f"get:{client_ip}", max_requests=120, window_seconds=60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests."})
    response = await call_next(request)
    return response

# ==================== PUBLIC LEGAL PAGES ====================
LEGAL_HTML_STYLE = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #121212; color: #ccc; padding: 24px; max-width: 720px; margin: 0 auto; line-height: 1.7; }
  h1 { color: #4CAF50; font-size: 28px; margin-bottom: 8px; }
  .meta { color: #888; font-size: 13px; margin-bottom: 32px; }
  h2 { color: #4CAF50; font-size: 18px; margin: 28px 0 10px; }
  p { margin-bottom: 12px; font-size: 15px; }
  a { color: #4CAF50; }
  .logo { text-align: center; margin-bottom: 24px; }
  .logo span { font-size: 36px; font-weight: bold; color: #fff; }
  .footer { border-top: 1px solid #333; margin-top: 40px; padding-top: 20px; text-align: center; color: #666; font-size: 12px; }
</style>
"""

@app.get("/legal/terms", response_class=HTMLResponse)
@app.get("/api/legal/terms", response_class=HTMLResponse)
async def public_terms(lang: str = "en"):
    if lang == "pt":
        content = """
<h1>Termos de Uso</h1>
<p class="meta">Última atualização: Junho 2025</p>
<h2>1. Aceitação dos Termos</h2>
<p>Ao baixar, instalar ou usar o BizRealms ("o Aplicativo"), você concorda em ficar vinculado a estes Termos de Uso.</p>
<h2>2. Descrição do Serviço</h2>
<p>BizRealms é um jogo de simulação de negócios onde os jogadores gerenciam empresas virtuais, investimentos, empregos e ativos. A moeda e os ativos do jogo não possuem valor monetário real, exceto quando explicitamente declarado em nosso programa de recompensas.</p>
<h2>3. Registro de Conta</h2>
<p>Você deve fornecer informações precisas ao criar uma conta. É permitida apenas uma conta por pessoa.</p>
<h2>4. Compras no Aplicativo</h2>
<p>O Aplicativo pode oferecer compras processadas via Stripe. Todas as compras são finais e não reembolsáveis, exceto conforme exigido pela legislação aplicável.</p>
<h2>5. Recompensas em Dinheiro Real</h2>
<p>O BizRealms pode oferecer recompensas em dinheiro real (USD) para jogadores com melhor ranking.</p>
<h2>6. Conduta Proibida</h2>
<p>Você não pode: usar trapaças, exploits ou automação; criar múltiplas contas; assediar outros jogadores; ou fazer engenharia reversa do Aplicativo.</p>
<h2>7. Propriedade Intelectual</h2>
<p>Todo conteúdo do BizRealms é de propriedade do BizRealms ou seus licenciadores.</p>
<h2>8. Rescisão</h2>
<p>Podemos suspender ou encerrar sua conta a qualquer momento por violação destes termos.</p>
<h2>9. Limitação de Responsabilidade</h2>
<p>O BizRealms é fornecido "como está" sem garantias.</p>
<h2>10. Contato</h2>
<p>Para questões: <a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    elif lang == "es":
        content = """
<h1>Términos de Uso</h1>
<p class="meta">Última actualización: Junio 2025</p>
<h2>1. Aceptación</h2><p>Al usar BizRealms, acepta estos Términos de Uso.</p>
<h2>2. Descripción</h2><p>BizRealms es un juego de simulación de negocios. La moneda del juego no tiene valor real.</p>
<h2>3. Cuenta</h2><p>Debe proporcionar información precisa. Una cuenta por persona.</p>
<h2>4. Compras</h2><p>Las compras son finales y no reembolsables.</p>
<h2>5. Recompensas</h2><p>Puede ofrecer recompensas en USD a los mejores jugadores.</p>
<h2>6. Conducta</h2><p>No use trampas, exploits o automatización.</p>
<h2>7. Contacto</h2><p><a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    elif lang == "de":
        content = """
<h1>Nutzungsbedingungen</h1>
<p class="meta">Letzte Aktualisierung: Juni 2025</p>
<h2>1. Akzeptanz</h2><p>Durch die Nutzung von BizRealms stimmen Sie diesen Bedingungen zu.</p>
<h2>2. Beschreibung</h2><p>BizRealms ist ein Geschäftssimulationsspiel. Die Spielwährung hat keinen realen Wert.</p>
<h2>3. Konto</h2><p>Geben Sie genaue Informationen an. Ein Konto pro Person.</p>
<h2>4. Käufe</h2><p>Alle Käufe sind endgültig.</p>
<h2>5. Belohnungen</h2><p>Top-Spieler können USD-Belohnungen erhalten.</p>
<h2>6. Kontakt</h2><p><a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    elif lang == "fr":
        content = """
<h1>Conditions d'Utilisation</h1>
<p class="meta">Dernière mise à jour : Juin 2025</p>
<h2>1. Acceptation</h2><p>En utilisant BizRealms, vous acceptez ces conditions.</p>
<h2>2. Description</h2><p>BizRealms est un jeu de simulation d'entreprise. La monnaie du jeu n'a pas de valeur réelle.</p>
<h2>3. Compte</h2><p>Fournissez des informations exactes. Un compte par personne.</p>
<h2>4. Achats</h2><p>Tous les achats sont définitifs.</p>
<h2>5. Récompenses</h2><p>Les meilleurs joueurs peuvent recevoir des récompenses en USD.</p>
<h2>6. Contact</h2><p><a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    elif lang == "it":
        content = """
<h1>Termini di Utilizzo</h1>
<p class="meta">Ultimo aggiornamento: Giugno 2025</p>
<h2>1. Accettazione</h2><p>Utilizzando BizRealms, accetti questi termini.</p>
<h2>2. Descrizione</h2><p>BizRealms è un gioco di simulazione aziendale. La valuta di gioco non ha valore reale.</p>
<h2>3. Account</h2><p>Fornisci informazioni accurate. Un account per persona.</p>
<h2>4. Acquisti</h2><p>Tutti gli acquisti sono definitivi.</p>
<h2>5. Ricompense</h2><p>I migliori giocatori possono ricevere ricompense in USD.</p>
<h2>6. Contatto</h2><p><a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    elif lang == "zh":
        content = """
<h1>使用条款</h1>
<p class="meta">最后更新：2025年6月</p>
<h2>1. 接受条款</h2><p>使用BizRealms即表示您同意这些条款。</p>
<h2>2. 服务描述</h2><p>BizRealms是一款商业模拟游戏。游戏货币没有真实价值。</p>
<h2>3. 账户</h2><p>请提供准确信息。每人一个账户。</p>
<h2>4. 购买</h2><p>所有购买均为最终交易。</p>
<h2>5. 奖励</h2><p>顶级玩家可获得美元奖励。</p>
<h2>6. 联系方式</h2><p><a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    else:
        content = """
<h1>Terms of Use</h1>
<p class="meta">Last updated: June 2025</p>
<h2>1. Acceptance</h2>
<p>By downloading, installing, or using BizRealms ("the App"), you agree to be bound by these Terms of Use.</p>
<h2>2. Description</h2>
<p>BizRealms is a business simulation game where players manage virtual companies, investments, jobs, and assets. In-game currency has no real monetary value except as explicitly stated in our rewards program.</p>
<h2>3. Account</h2>
<p>You must provide accurate information. One account per person.</p>
<h2>4. In-App Purchases</h2>
<p>Purchases are processed via Stripe. All purchases are final and non-refundable except as required by applicable law.</p>
<h2>5. Real Money Rewards</h2>
<p>BizRealms may offer real money rewards (USD) to top-ranking players.</p>
<h2>6. Prohibited Conduct</h2>
<p>You may not: use cheats, exploits, or automation; create multiple accounts; harass other players; or reverse-engineer the App.</p>
<h2>7. Intellectual Property</h2>
<p>All BizRealms content is owned by BizRealms or its licensors.</p>
<h2>8. Termination</h2>
<p>We may suspend or terminate your account at any time for violation of these terms.</p>
<h2>9. Limitation of Liability</h2>
<p>BizRealms is provided "as is" without warranties.</p>
<h2>10. Contact</h2>
<p><a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>
"""
    return HTMLResponse(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BizRealms - Terms</title>{LEGAL_HTML_STYLE}</head><body>
<div class="logo"><span>BizRealms</span></div>
{content}
<div class="footer">&copy; 2025 BizRealms.</div>
</body></html>""")

@app.get("/legal/privacy", response_class=HTMLResponse)
@app.get("/api/legal/privacy", response_class=HTMLResponse)
async def public_privacy(lang: str = "en"):
    if lang == "pt":
        content = """
<h1>Política de Privacidade</h1>
<p class="meta">Última atualização: Junho 2025</p>
<h2>1. Informações Coletadas</h2>
<p>Nome, e-mail, dados de perfil, progresso do jogo, dados do dispositivo.</p>
<h2>2. Uso</h2>
<p>Gerenciamento de conta, processamento de compras/recompensas (USD), rankings, prevenção de fraudes.</p>
<h2>3. Compartilhamento</h2>
<p>Não vendemos dados. Compartilhamos com processadores de pagamento (Stripe/PayPal) e provedores de análise (dados anonimizados).</p>
<h2>4. Segurança</h2>
<p>Criptografia, JWT, bcrypt, autenticação biométrica opcional.</p>
<h2>5. Seus Direitos</h2>
<p>Acesse, corrija ou exclua seus dados a qualquer momento.</p>
<h2>6. Contato</h2>
<p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    elif lang == "es":
        content = """
<h1>Política de Privacidad</h1>
<p class="meta">Última actualización: Junio 2025</p>
<h2>1. Datos Recopilados</h2><p>Nombre, email, datos de juego, datos del dispositivo.</p>
<h2>2. Uso</h2><p>Gestión de cuenta, procesamiento de pagos (USD), rankings.</p>
<h2>3. Seguridad</h2><p>Cifrado, JWT, bcrypt.</p>
<h2>4. Contacto</h2><p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    elif lang == "de":
        content = """
<h1>Datenschutzrichtlinie</h1>
<p class="meta">Letzte Aktualisierung: Juni 2025</p>
<h2>1. Gesammelte Daten</h2><p>Name, E-Mail, Spieldaten, Gerätedaten.</p>
<h2>2. Verwendung</h2><p>Kontoverwaltung, Zahlungsabwicklung (USD), Rankings.</p>
<h2>3. Sicherheit</h2><p>Verschlüsselung, JWT, bcrypt.</p>
<h2>4. Kontakt</h2><p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    elif lang == "fr":
        content = """
<h1>Politique de Confidentialité</h1>
<p class="meta">Dernière mise à jour : Juin 2025</p>
<h2>1. Données Collectées</h2><p>Nom, email, données de jeu, données d'appareil.</p>
<h2>2. Utilisation</h2><p>Gestion de compte, traitement des paiements (USD), classements.</p>
<h2>3. Sécurité</h2><p>Chiffrement, JWT, bcrypt.</p>
<h2>4. Contact</h2><p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    elif lang == "it":
        content = """
<h1>Politica sulla Privacy</h1>
<p class="meta">Ultimo aggiornamento: Giugno 2025</p>
<h2>1. Dati Raccolti</h2><p>Nome, email, dati di gioco, dati del dispositivo.</p>
<h2>2. Utilizzo</h2><p>Gestione account, pagamenti (USD), classifiche.</p>
<h2>3. Sicurezza</h2><p>Crittografia, JWT, bcrypt.</p>
<h2>4. Contatto</h2><p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    elif lang == "zh":
        content = """
<h1>隐私政策</h1>
<p class="meta">最后更新：2025年6月</p>
<h2>1. 收集的数据</h2><p>姓名、电子邮件、游戏数据、设备数据。</p>
<h2>2. 使用目的</h2><p>账户管理、支付处理（美元）、排行榜。</p>
<h2>3. 安全性</h2><p>加密、JWT、bcrypt。</p>
<h2>4. 联系方式</h2><p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    else:
        content = """
<h1>Privacy Policy</h1>
<p class="meta">Last updated: June 2025</p>
<h2>1. Information We Collect</h2>
<p>Name, email, profile data, gameplay data (progress, transactions, rankings), device data.</p>
<h2>2. How We Use Your Information</h2>
<p>Account management, processing purchases and rewards (USD), maintaining rankings, preventing fraud.</p>
<h2>3. Information Sharing</h2>
<p>We do not sell your personal information. We share limited data with payment processors (Stripe/PayPal) and analytics providers (anonymized data).</p>
<h2>4. Data Security</h2>
<p>We implement industry-standard security measures including encryption, JWT authentication, bcrypt password hashing, and optional biometric authentication.</p>
<h2>5. Your Rights</h2>
<p>You have the right to access, correct, or delete your personal data at any time.</p>
<h2>6. Contact</h2>
<p><a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a></p>
"""
    return HTMLResponse(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BizRealms - Privacy</title>{LEGAL_HTML_STYLE}</head><body>
<div class="logo"><span>BizRealms</span></div>
{content}
<div class="footer">&copy; 2025 BizRealms.</div>
</body></html>""")

# ==================== ROOT ENDPOINT ====================
@api_router.get("/")
async def root():
    return {"message": "BizRealms API", "version": "2.0.0"}

@api_router.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment."""
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected", "version": "2.0.0"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "disconnected"})

# ==================== IMPORT & INCLUDE ROUTE MODULES ====================
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.jobs import router as jobs_router
from routes.investments import router as investments_router
from routes.companies import router as companies_router
from routes.assets import router as assets_router
from routes.rankings import router as rankings_router
from routes.store import router as store_router
from routes.bank import router as bank_router
from routes.market import router as market_router
from routes.notifications import router as notifications_router
from routes.events import router as events_router
from routes.phases import router as phases_router
from routes.prestige import router as prestige_router
from routes.competitions import router as competitions_router

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(jobs_router)
api_router.include_router(investments_router)
api_router.include_router(companies_router)
api_router.include_router(assets_router)
api_router.include_router(rankings_router)
api_router.include_router(store_router)
api_router.include_router(bank_router)
api_router.include_router(market_router)
api_router.include_router(notifications_router)
api_router.include_router(events_router)
api_router.include_router(phases_router)
api_router.include_router(prestige_router)
api_router.include_router(competitions_router)

# Include the api_router in the main app
app.include_router(api_router)

# ==================== STARTUP EVENTS ====================
from routes.investments import startup_investments
from routes.companies import startup_map, startup_companies
from routes.assets import startup_assets


# ==================== PUBLIC PAGES ====================
@app.get("/delete-account", response_class=HTMLResponse)
async def delete_account_page():
    """Public page for account deletion instructions (required by Google Play)."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BizRealms - Exclusão de Conta</title>
<style>body{font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#1a1a2e;color:#e0e0e0}
h1{color:#FFD700}h2{color:#4A90D9}a{color:#FFD700}.box{background:#222238;border-radius:12px;padding:20px;margin:16px 0}
.btn{display:inline-block;background:#FF5722;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;margin-top:12px}</style>
</head><body>
<h1>🎮 BizRealms</h1>
<h2>Exclusão de Conta e Dados</h2>
<div class="box">
<p><strong>Para solicitar a exclusão da sua conta BizRealms e todos os dados associados, siga os passos:</strong></p>
<ol>
<li>Abra o app <strong>BizRealms</strong></li>
<li>Vá em <strong>Perfil</strong> (ícone no canto inferior direito)</li>
<li>Role até <strong>"Configurações da Conta"</strong></li>
<li>Toque em <strong>"Excluir Conta"</strong></li>
<li>Confirme a exclusão</li>
</ol>
<p>Ou envie um email para: <a href="mailto:suporte@bizrealms.com">suporte@bizrealms.com</a> com o assunto "Excluir minha conta" e o email cadastrado.</p>
</div>
<div class="box">
<h3>Dados que serão excluídos:</h3>
<ul>
<li>✅ Dados pessoais (nome, email, senha)</li>
<li>✅ Progresso do jogo (empresas, investimentos, ativos)</li>
<li>✅ Histórico de transações no jogo</li>
<li>✅ Configurações e preferências</li>
</ul>
<h3>Prazo de exclusão:</h3>
<p>Todos os dados são excluídos <strong>imediatamente</strong> após a confirmação.</p>
</div>
<p style="color:#888;font-size:12px;margin-top:24px">© 2025 BizRealms. Todos os direitos reservados.</p>
</body></html>""")

@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy_page():
    """Public privacy policy page (required by Google Play)."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BizRealms - Política de Privacidade</title>
<style>body{font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#1a1a2e;color:#e0e0e0}
h1{color:#FFD700}h2{color:#4A90D9}h3{color:#E6A817}.box{background:#222238;border-radius:12px;padding:20px;margin:16px 0}
a{color:#FFD700}</style>
</head><body>
<h1>🎮 BizRealms</h1>
<h2>Política de Privacidade</h2>
<p><em>Última atualização: Abril 2025</em></p>

<div class="box">
<h3>1. Dados Coletados</h3>
<ul>
<li><strong>Dados de cadastro:</strong> Nome de usuário, endereço de email, senha (criptografada)</li>
<li><strong>Dados do jogo:</strong> Progresso, empresas, investimentos, ativos virtuais</li>
<li><strong>Dados de uso:</strong> Logs de acesso, dispositivo, sistema operacional</li>
<li><strong>Dados de publicidade:</strong> ID de publicidade do dispositivo (Google Advertising ID)</li>
</ul>
</div>

<div class="box">
<h3>2. Uso dos Dados</h3>
<ul>
<li>Prover e manter o funcionamento do jogo</li>
<li>Personalizar a experiência do jogador</li>
<li>Exibir anúncios personalizados (Google AdMob)</li>
<li>Análise de erros e melhorias (Sentry)</li>
<li>Comunicações sobre o jogo (notificações push)</li>
</ul>
</div>

<div class="box">
<h3>3. Compartilhamento de Dados</h3>
<p>Compartilhamos dados com os seguintes serviços terceiros:</p>
<ul>
<li><strong>Google AdMob:</strong> Para exibição de anúncios</li>
<li><strong>Sentry:</strong> Para monitoramento de erros</li>
<li><strong>Railway:</strong> Hospedagem do servidor</li>
<li><strong>MongoDB Atlas:</strong> Armazenamento de dados</li>
</ul>
<p>Não vendemos dados pessoais a terceiros.</p>
</div>

<div class="box">
<h3>4. Segurança</h3>
<p>Todos os dados são transmitidos via HTTPS (criptografia em trânsito). Senhas são armazenadas com hash bcrypt.</p>
</div>

<div class="box">
<h3>5. Seus Direitos</h3>
<ul>
<li>Acessar seus dados pessoais</li>
<li>Corrigir dados incorretos</li>
<li>Solicitar exclusão da conta e dados</li>
<li>Revogar consentimento de uso de dados</li>
</ul>
<p>Para exercer seus direitos, acesse as configurações do app ou envie email para: <a href="mailto:suporte@bizrealms.com">suporte@bizrealms.com</a></p>
</div>

<div class="box">
<h3>6. Retenção de Dados</h3>
<p>Seus dados são mantidos enquanto a conta estiver ativa. Ao excluir a conta, todos os dados são removidos imediatamente.</p>
</div>

<div class="box">
<h3>7. Menores de Idade</h3>
<p>O BizRealms é destinado a maiores de 13 anos. Não coletamos intencionalmente dados de menores de 13 anos.</p>
</div>

<div class="box">
<h3>8. Alterações</h3>
<p>Esta política pode ser atualizada periodicamente. Notificaremos os usuários sobre mudanças significativas através do app.</p>
</div>

<div class="box">
<h3>9. Contato</h3>
<p>Email: <a href="mailto:suporte@bizrealms.com">suporte@bizrealms.com</a></p>
<p>Desenvolvedor: BizRealms</p>
</div>

<p style="color:#888;font-size:12px;margin-top:24px">© 2025 BizRealms. Todos os direitos reservados.</p>
</body></html>""")


@app.on_event("startup")
async def on_startup():
    """Run all startup seed functions."""
    await startup_investments()
    await startup_map()
    await startup_companies()
    await startup_assets()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
