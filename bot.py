
import requests
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime

# --- CONFIGURAÇÕES TELEGRAM ---
TELEGRAM_TOKEN = '7474571490:AAFEE8efexplZ7t0QyA2UiTbn4j3PYae8jw'
CHAT_ID = '5803697819'

def enviar_mensagem(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': mensagem}
        resposta = requests.post(url, data=payload)
        if resposta.status_code == 200:
            print("✅ Mensagem enviada com sucesso!")
        else:
            print("❌ Erro ao enviar mensagem:", resposta.status_code)
    except Exception as e:
        print("❌ Erro ao enviar mensagem:", e)

def obter_dados_btc(limite=100, tentativas=5, atraso=10):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "1"}

    for tentativa in range(tentativas):
        try:
            resposta = requests.get(url, params=params, timeout=30)
            if resposta.status_code == 200:
                dados = resposta.json()["prices"][-limite:]
                df = pd.DataFrame(dados, columns=["timestamp", "close"])
                df["close"] = pd.to_numeric(df["close"])
                print(f"✅ Dados obtidos! Preço atual: ${df['close'].iloc[-1]:.2f}")
                return df
            elif resposta.status_code == 429:
                print(f"⚠️ Rate limit atingido. Aguardando {atraso * 2}s...")
                time.sleep(atraso * 2)
            else:
                print(f"⚠️ Erro HTTP: {resposta.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro de requisição (tentativa {tentativa + 1}): {e}")
        if tentativa < tentativas - 1:
            print(f"🔄 Tentando novamente em {atraso}s...")
            time.sleep(atraso)
    print("❌ Não foi possível obter dados.")
    return None

def analisar_mercado():
    df = obter_dados_btc()
    if df is None or df.empty:
        print("❌ Sem dados de mercado.")
        return None

    try:
        df["RSI"] = ta.rsi(df["close"], length=14)
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        df["EMA9"] = ta.ema(df["close"], length=9)
        df["EMA21"] = ta.ema(df["close"], length=21)
        df["Volume"] = df["close"].diff().abs()
        df["MediaVolume"] = df["Volume"].rolling(20).mean()

        rsi = df["RSI"].iloc[-1]
        macd_valor = df["MACD_12_26_9"].iloc[-1]
        sinal_macd = df["MACDs_12_26_9"].iloc[-1]
        histograma = df["MACDh_12_26_9"].iloc[-1]
        histograma_ant = df["MACDh_12_26_9"].iloc[-2]

        ema9 = df["EMA9"].iloc[-1]
        ema21 = df["EMA21"].iloc[-1]
        ema9_ant = df["EMA9"].iloc[-2]
        ema21_ant = df["EMA21"].iloc[-2]

        preco = df["close"].iloc[-1]
        volume = df["Volume"].iloc[-1]
        media_volume = df["MediaVolume"].iloc[-1]

        # Cruzamento de médias
        cruzou_cima = ema9_ant < ema21_ant and ema9 > ema21
        cruzou_baixo = ema9_ant > ema21_ant and ema9 < ema21
        hist_subindo = histograma > histograma_ant
        hist_caindo = histograma < histograma_ant

        # Novo critério otimizado
        sinal_compra = (
            rsi > 55 and
            macd_valor > sinal_macd and
            cruzou_cima and
            hist_subindo
        )

        sinal_venda = (
            rsi < 45 and
            macd_valor < sinal_macd and
            cruzou_baixo and
            hist_caindo
        )

        if sinal_compra:
            sinal = "🟢 SCALP COMPRA - TARGET 100 PONTOS"
            emoji = "⚡"
        elif sinal_venda:
            sinal = "🔴 SCALP VENDA - TARGET 100 PONTOS"
            emoji = "⚡"
        else:
            print("⏳ Nenhum sinal forte no momento.")
            return None

        mensagem = f"""{emoji} {sinal} {emoji}

📊 BTC/USD:
💰 Preço: ${preco:.2f}
📈 RSI: {rsi:.2f}
📉 MACD: {macd_valor:.4f}
🔁 Sinal MACD: {sinal_macd:.4f}
📊 EMA 9: {ema9:.2f}
📊 EMA 21: {ema21:.2f}
📈 Histograma: {histograma:.4f}
📦 Volume: {volume:.2f} | Média: {media_volume:.2f}

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""

        return mensagem

    except Exception as e:
        print(f"⚠️ Erro nos cálculos: {e}")
        return None

def executar_bot():
    print("🤖 Bot iniciado - SCALP 100 PONTOS")
    enviar_mensagem("⚡ Bot ATIVO! | Estratégia SCALP BTC | Intervalo: 2min")

    intervalo_analise = 120
    ultimo_sinal = None
    heartbeat = 0

    while True:
        try:
            print(f"\n🔍 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Analisando...")
            resultado = analisar_mercado()

            if resultado and resultado != ultimo_sinal:
                enviar_mensagem(resultado)
                ultimo_sinal = resultado
                heartbeat = 0
            else:
                heartbeat += 1
                print("📉 Nenhuma nova entrada.")

            if heartbeat >= 30:
                enviar_mensagem(f"💓 Bot ativo às {datetime.now().strftime('%H:%M')}")
                heartbeat = 0

            time.sleep(intervalo_analise)

        except KeyboardInterrupt:
            enviar_mensagem("🛑 Bot PARADO pelo usuário.")
            print("Encerrado.")
            break
        except Exception as e:
            print(f"⚠️ Erro crítico: {e}")
            enviar_mensagem(f"⚠️ Erro no bot: {str(e)[:100]}")
            time.sleep(60)

# --- Iniciar ---
if __name__ == "__main__":
    executar_bot()
