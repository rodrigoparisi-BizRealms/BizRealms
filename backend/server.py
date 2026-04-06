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
async def public_terms():
    return HTMLResponse(f"""<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BizRealms - Termos de Uso</title>{LEGAL_HTML_STYLE}</head><body>
<div class="logo"><span>BizRealms</span></div>
<h1>Termos de Uso / Terms of Use</h1>
<p class="meta">Última atualização: Junho 2025</p>

<h2>1. Aceitação dos Termos</h2>
<p>Ao baixar, instalar ou usar o BizRealms ("o Aplicativo"), você concorda em ficar vinculado a estes Termos de Uso. Se você não concordar, não use o Aplicativo.</p>

<h2>2. Descrição do Serviço</h2>
<p>BizRealms é um jogo de simulação de negócios onde os jogadores gerenciam empresas virtuais, investimentos, empregos e ativos. A moeda e os ativos do jogo não possuem valor monetário real, exceto quando explicitamente declarado em nosso programa de recompensas.</p>

<h2>3. Registro de Conta</h2>
<p>Você deve fornecer informações precisas ao criar uma conta. Você é responsável por manter a segurança de suas credenciais. É permitida apenas uma conta por pessoa.</p>

<h2>4. Compras no Aplicativo</h2>
<p>O Aplicativo pode oferecer compras processadas via Stripe. Todas as compras são finais e não reembolsáveis, exceto conforme exigido pela legislação aplicável. Itens virtuais comprados não possuem valor no mundo real.</p>

<h2>5. Recompensas em Dinheiro Real</h2>
<p>O BizRealms pode oferecer recompensas em dinheiro real para jogadores com melhor ranking. Elegibilidade, valores e métodos de pagamento são determinados pelo BizRealms a seu exclusivo critério. Os jogadores devem fornecer informações válidas de pagamento (ex: conta PayPal e documento de identidade) para receber recompensas.</p>

<h2>6. Conduta Proibida</h2>
<p>Você não pode: usar trapaças, exploits ou automação; criar múltiplas contas; assediar outros jogadores; tentar manipular rankings; ou fazer engenharia reversa do Aplicativo.</p>

<h2>7. Propriedade Intelectual</h2>
<p>Todo conteúdo, gráficos, logos e software do BizRealms são de propriedade do BizRealms ou seus licenciadores e são protegidos por leis de propriedade intelectual.</p>

<h2>8. Anúncios</h2>
<p>O Aplicativo pode exibir anúncios como parte do modelo de monetização. Os jogadores podem assistir anúncios para obter benefícios no jogo. A exibição está sujeita à disponibilidade da rede de anúncios.</p>

<h2>9. Rescisão</h2>
<p>Podemos suspender ou encerrar sua conta a qualquer momento por violação destes termos ou por qualquer outro motivo a nosso critério.</p>

<h2>10. Limitação de Responsabilidade</h2>
<p>O BizRealms é fornecido "como está" sem garantias. Não somos responsáveis por danos indiretos, incidentais ou consequenciais decorrentes do uso do Aplicativo.</p>

<h2>11. Lei Aplicável</h2>
<p>Estes Termos são regidos pelas leis da República Federativa do Brasil. Quaisquer disputas serão resolvidas no foro da comarca do desenvolvedor.</p>

<h2>12. Alterações nos Termos</h2>
<p>Podemos atualizar estes termos a qualquer momento. O uso continuado do Aplicativo após as alterações constitui aceitação dos novos termos.</p>

<h2>13. Contato</h2>
<p>Para questões sobre estes Termos: <a href="mailto:support@bizrealms.com">support@bizrealms.com</a></p>

<div class="footer">&copy; 2025 BizRealms. Todos os direitos reservados. | <a href="/legal/privacy">Política de Privacidade</a></div>
</body></html>""")

@app.get("/legal/privacy", response_class=HTMLResponse)
@app.get("/api/legal/privacy", response_class=HTMLResponse)
async def public_privacy():
    return HTMLResponse(f"""<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BizRealms - Política de Privacidade</title>{LEGAL_HTML_STYLE}</head><body>
<div class="logo"><span>BizRealms</span></div>
<h1>Política de Privacidade / Privacy Policy</h1>
<p class="meta">Última atualização: Junho 2025</p>

<h2>1. Informações que Coletamos</h2>
<p>Coletamos informações fornecidas diretamente por você: nome, endereço de e-mail e dados opcionais de perfil (avatar, cidade). Também coletamos dados de jogabilidade (progresso, transações, rankings), dados do dispositivo (SO, idioma, fuso horário) e documento de identidade (quando necessário para saques via PayPal).</p>

<h2>2. Como Usamos Suas Informações</h2>
<p>Usamos suas informações para: fornecer e melhorar a experiência do jogo; gerenciar sua conta; processar compras e recompensas no app; manter rankings; enviar notificações sobre eventos do jogo; e prevenir fraudes e abusos.</p>

<h2>3. Compartilhamento de Informações</h2>
<p>Não vendemos suas informações pessoais. Podemos compartilhar dados limitados com: processadores de pagamento (para compras e recompensas via PayPal/Stripe); provedores de análise (dados agregados e anonimizados); redes de anúncios (identificadores anonimizados); e autoridades legais (quando exigido por lei).</p>

<h2>4. Segurança dos Dados</h2>
<p>Implementamos medidas de segurança padrão da indústria, incluindo criptografia, autenticação segura (JWT), hash de senhas (bcrypt), autenticação biométrica opcional e auditorias regulares de segurança.</p>

<h2>5. Seus Direitos (LGPD - Lei nº 13.709/2018)</h2>
<p>De acordo com a Lei Geral de Proteção de Dados, você tem o direito de: acessar seus dados pessoais; corrigir dados incorretos; solicitar a exclusão de sua conta e dados associados (use "Zerar Conta" no perfil); exportar seus dados; revogar consentimento; e optar por não receber comunicações de marketing.</p>

<h2>6. Armazenamento Local</h2>
<p>O aplicativo utiliza armazenamento local para tokens de autenticação e preferências do usuário (tema, idioma, sons). Não utilizamos cookies de rastreamento de terceiros.</p>

<h2>7. Privacidade de Menores</h2>
<p>O BizRealms não é destinado a menores de 13 anos (ou a idade mínima em sua jurisdição). Não coletamos intencionalmente dados de crianças.</p>

<h2>8. Transferência Internacional de Dados</h2>
<p>Seus dados podem ser processados em servidores localizados fora do seu país. Garantimos salvaguardas apropriadas conforme exigido pela LGPD.</p>

<h2>9. Retenção de Dados</h2>
<p>Mantemos seus dados enquanto sua conta estiver ativa. Após a exclusão, podemos reter dados anonimizados por até 90 dias para fins de análise.</p>

<h2>10. Anúncios e Monetização</h2>
<p>O BizRealms pode exibir anúncios. Os dados compartilhados com redes de anúncios são limitados a identificadores anonimizados. Uma parcela da receita (5%) é distribuída aos jogadores com melhor ranking.</p>

<h2>11. Alterações nesta Política</h2>
<p>Podemos atualizar esta política periodicamente. Notificaremos sobre mudanças significativas através do aplicativo.</p>

<h2>12. Contato e Encarregado (DPO)</h2>
<p>Para questões de privacidade: <a href="mailto:privacy@bizrealms.com">privacy@bizrealms.com</a><br>
Encarregado de Proteção de Dados (DPO): <a href="mailto:dpo@bizrealms.com">dpo@bizrealms.com</a></p>

<div class="footer">&copy; 2025 BizRealms. Todos os direitos reservados. | <a href="/legal/terms">Termos de Uso</a></div>
</body></html>""")

# ==================== ROOT ENDPOINT ====================
@api_router.get("/")
async def root():
    return {"message": "BizRealms API", "version": "2.0.0"}

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
