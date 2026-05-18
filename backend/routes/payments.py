"""BizRealms - Stripe Connect Automatic Payments for Prize Winners"""
import os
import stripe
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from database import db
from utils import get_current_user
from dotenv import load_dotenv
import uuid

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
FRONTEND_URL = os.getenv('EXPO_PUBLIC_FRONTEND_URL', 'https://bizrealms-production-ead0.up.railway.app')


# ==================== STRIPE CONNECT ONBOARDING ====================

@router.post("/payments/create-connect-account")
async def create_connect_account(current_user: dict = Depends(get_current_user)):
    """Create a Stripe Connect Express account for the player to receive payments."""
    user = await db.users.find_one({"id": current_user['id']})
    
    # Check if user already has a Stripe Connect account
    stripe_account_id = user.get('stripe_connect_id')
    
    if stripe_account_id:
        # Check if account is already fully onboarded
        try:
            account = stripe.Account.retrieve(stripe_account_id)
            if account.charges_enabled and account.payouts_enabled:
                return {
                    "success": True,
                    "message": "Conta Stripe já configurada e ativa!",
                    "already_onboarded": True,
                    "account_id": stripe_account_id,
                }
            else:
                # Account exists but not fully onboarded - create new link
                account_link = stripe.AccountLink.create(
                    account=stripe_account_id,
                    refresh_url=f"{FRONTEND_URL}/api/payments/connect-refresh",
                    return_url=f"{FRONTEND_URL}/api/payments/connect-success?user_id={current_user['id']}",
                    type="account_onboarding",
                )
                return {
                    "success": True,
                    "onboarding_url": account_link.url,
                    "message": "Complete o cadastro para receber pagamentos.",
                }
        except stripe.error.InvalidRequestError:
            # Account was deleted or invalid, create new one
            pass

    # Create new Stripe Connect Express account
    try:
        account = stripe.Account.create(
            type="express",
            country=user.get('country_code', 'BR'),
            email=user.get('email'),
            capabilities={
                "transfers": {"requested": True},
            },
            business_type="individual",
            metadata={
                "bizrealms_user_id": current_user['id'],
                "bizrealms_user_name": user.get('name', ''),
            },
        )

        # Save Stripe Connect ID to user
        await db.users.update_one({"id": current_user['id']}, {
            "$set": {
                "stripe_connect_id": account.id,
                "stripe_connect_created_at": datetime.utcnow(),
            }
        })

        # Create onboarding link
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{FRONTEND_URL}/api/payments/connect-refresh",
            return_url=f"{FRONTEND_URL}/api/payments/connect-success?user_id={current_user['id']}",
            type="account_onboarding",
        )

        return {
            "success": True,
            "onboarding_url": account_link.url,
            "account_id": account.id,
            "message": "Abra o link para configurar sua conta de pagamento.",
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Connect error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar conta de pagamento: {str(e)}")


@router.get("/payments/connect-status")
async def get_connect_status(current_user: dict = Depends(get_current_user)):
    """Check if user's Stripe Connect account is ready to receive payments."""
    user = await db.users.find_one({"id": current_user['id']})
    stripe_account_id = user.get('stripe_connect_id')

    if not stripe_account_id:
        return {
            "connected": False,
            "message": "Conta de pagamento não configurada. Configure para receber prêmios!",
        }

    try:
        account = stripe.Account.retrieve(stripe_account_id)
        is_ready = account.charges_enabled and account.payouts_enabled

        return {
            "connected": True,
            "ready": is_ready,
            "account_id": stripe_account_id,
            "email": account.get('email', ''),
            "country": account.get('country', ''),
            "payouts_enabled": account.payouts_enabled,
            "charges_enabled": account.charges_enabled,
            "message": "Conta ativa! Pronta para receber pagamentos." if is_ready else "Conta pendente. Complete o cadastro.",
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe status check error: {e}")
        return {"connected": False, "message": "Erro ao verificar conta de pagamento."}


# ==================== AUTOMATIC PRIZE PAYMENT ====================

@router.post("/payments/send-prize")
async def send_prize_payment(request: dict, current_user: dict = Depends(get_current_user)):
    """Automatically send prize money to a winner via Stripe Connect.
    Called when a player clicks 'Claim Prize'."""
    reward_id = request.get('reward_id')
    if not reward_id:
        raise HTTPException(status_code=400, detail="reward_id é obrigatório.")

    # Get the reward
    reward = await db.real_money_rewards.find_one({
        "id": reward_id,
        "user_id": current_user['id'],
        "status": "pending_claim",
    })
    if not reward:
        raise HTTPException(status_code=404, detail="Recompensa não encontrada ou já resgatada.")

    # Check if user has Stripe Connect account ready
    user = await db.users.find_one({"id": current_user['id']})
    stripe_account_id = user.get('stripe_connect_id')

    if not stripe_account_id:
        raise HTTPException(
            status_code=400,
            detail="Configure sua conta de pagamento primeiro! Vá em Perfil → Conta de Pagamento."
        )

    # Verify account is ready
    try:
        account = stripe.Account.retrieve(stripe_account_id)
        if not account.payouts_enabled:
            raise HTTPException(
                status_code=400,
                detail="Sua conta de pagamento ainda não está ativa. Complete o cadastro Stripe."
            )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Erro ao verificar conta: {str(e)}")

    # Convert amount to cents (Stripe uses smallest currency unit)
    amount_usd = reward['amount']
    amount_cents = int(amount_usd * 100)

    if amount_cents < 100:  # Minimum $1.00
        raise HTTPException(status_code=400, detail="Valor mínimo para pagamento: $ 1.00")

    # Create the transfer
    try:
        transfer = stripe.Transfer.create(
            amount=amount_cents,
            currency="usd",
            destination=stripe_account_id,
            description=f"BizRealms Prize - {reward['month']} - Position #{reward['position']}",
            metadata={
                "reward_id": reward_id,
                "user_id": current_user['id'],
                "month": reward['month'],
                "position": str(reward['position']),
            },
        )

        # Update reward status
        await db.real_money_rewards.update_one({"id": reward_id}, {"$set": {
            "status": "paid",
            "paid_at": datetime.utcnow(),
            "stripe_transfer_id": transfer.id,
            "payment_method": "stripe_connect",
        }})

        # Notify player
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "type": "payment_completed",
            "title": "💰 Pagamento Enviado!",
            "message": f"Seu prêmio de $ {amount_usd:.2f} (#{reward['position']}º lugar - {reward['month']}) foi enviado para sua conta Stripe!",
            "read": False,
            "created_at": datetime.utcnow(),
        })

        logger.info(f"Prize payment sent: ${amount_usd} to {stripe_account_id} (transfer: {transfer.id})")

        return {
            "success": True,
            "message": f"Prêmio de $ {amount_usd:.2f} enviado com sucesso para sua conta!",
            "amount": amount_usd,
            "transfer_id": transfer.id,
            "position": reward['position'],
            "month": reward['month'],
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe transfer error: {e}")
        
        # Mark as failed
        await db.real_money_rewards.update_one({"id": reward_id}, {"$set": {
            "status": "payment_failed",
            "payment_error": str(e),
        }})
        
        raise HTTPException(status_code=500, detail=f"Erro no pagamento: {str(e)}")


# ==================== PAYMENT HISTORY ====================

@router.get("/payments/history")
async def get_payment_history(current_user: dict = Depends(get_current_user)):
    """Get player's payment history."""
    rewards = await db.real_money_rewards.find({
        "user_id": current_user['id']
    }).sort("created_at", -1).to_list(50)

    history = []
    for r in rewards:
        r.pop('_id', None)
        history.append({
            "id": r.get('id'),
            "month": r.get('month'),
            "position": r.get('position'),
            "amount": r.get('amount'),
            "status": r.get('status'),
            "paid_at": r.get('paid_at'),
            "stripe_transfer_id": r.get('stripe_transfer_id'),
            "created_at": r.get('created_at'),
        })

    return {"history": history, "total": len(history)}


# ==================== SUCCESS/REFRESH CALLBACKS ====================

from starlette.responses import HTMLResponse

@router.get("/payments/connect-success")
async def connect_success(user_id: str = ""):
    """Callback after Stripe Connect onboarding is completed."""
    if user_id:
        await db.users.update_one({"id": user_id}, {
            "$set": {"stripe_connect_onboarded_at": datetime.utcnow()}
        })
    
    return HTMLResponse("""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>BizRealms - Conta Configurada!</title>
<style>body{font-family:sans-serif;background:#1a1a2e;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center;padding:20px}
.box{max-width:400px}h1{color:#4CAF50;font-size:28px}p{color:#aaa;font-size:16px;line-height:1.6}</style></head>
<body><div class="box">
<h1>✅ Conta Configurada!</h1>
<p>Sua conta de pagamento foi configurada com sucesso. Agora você pode receber prêmios automaticamente no BizRealms!</p>
<p style="color:#FFD700;font-size:14px;margin-top:24px">Volte para o app e continue jogando! 🎮</p>
</div></body></html>""")


@router.get("/payments/connect-refresh")
async def connect_refresh():
    """Callback when Stripe Connect onboarding link expires."""
    return HTMLResponse("""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>BizRealms - Link Expirado</title>
<style>body{font-family:sans-serif;background:#1a1a2e;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center;padding:20px}
.box{max-width:400px}h1{color:#FF9800;font-size:28px}p{color:#aaa;font-size:16px;line-height:1.6}</style></head>
<body><div class="box">
<h1>⚠️ Link Expirado</h1>
<p>O link de configuração expirou. Volte para o app BizRealms e tente novamente em Perfil → Conta de Pagamento.</p>
</div></body></html>""")
