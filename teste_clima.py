#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para a API do clima
Executa independentemente do Flask para diagnosticar problemas
"""

import os
import json
import requests
from datetime import datetime

def testar_api_clima():
    print("🧪 TESTANDO API DO CLIMA")
    print("=" * 50)
    
    # Carregar configurações do .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Arquivo .env carregado")
    except ImportError:
        print("⚠️ python-dotenv não encontrado, usando variáveis do sistema")
    
    # Pegar configurações
    api_key = os.getenv('API_KEY', '4cd224af1c46c58cf99cdbd798e13931')
    city = os.getenv('CITY', 'Três Lagoas, BR')
    
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else 'CURTA'}")
    print(f"🏙️ Cidade: {city}")
    
    # Montar URL
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=pt_br'
    print(f"🌐 URL: {url[:80]}...")
    
    print("\n📡 Fazendo requisição...")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ ERRO 401: API Key inválida!")
            print("   Obtenha uma chave gratuita em: https://openweathermap.org/api")
            return False
        elif response.status_code == 404:
            print(f"❌ ERRO 404: Cidade '{city}' não encontrada!")
            print("   Verifique o nome da cidade no arquivo .env")
            return False
        elif response.status_code != 200:
            print(f"❌ ERRO HTTP {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return False
        
        # Processar resposta
        dados = response.json()
        
        # Verificar estrutura
        if 'list' not in dados or not dados['list']:
            print("❌ Resposta não contém dados de previsão")
            return False
        
        if 'city' not in dados:
            print("❌ Resposta não contém informações da cidade")
            return False
        
        # Mostrar dados
        primeira_previsao = dados['list'][0]
        print("\n✅ DADOS RECEBIDOS COM SUCESSO!")
        print(f"🏙️ Cidade: {dados['city']['name']}")
        print(f"🌡️ Temperatura: {primeira_previsao['main']['temp']:.1f}°C")
        print(f"🌤️ Condição: {primeira_previsao['weather'][0]['description']}")
        print(f"💧 Chance de chuva: {int(primeira_previsao['pop'] * 100)}%")
        print(f"💨 Vento: {round(primeira_previsao['wind']['speed'] * 3.6, 1)} km/h")
        
        # Salvar arquivo de teste
        cache_file = 'clima_teste.json'
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dados salvos em: {cache_file}")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Servidor demorou para responder")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO: Verifique sua internet")
        return False
    except json.JSONDecodeError:
        print("❌ ERRO: Resposta não é um JSON válido")
        return False
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

if __name__ == '__main__':
    sucesso = testar_api_clima()
    
    print("\n" + "=" * 50)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("   A API do clima está funcionando corretamente.")
    else:
        print("💥 TESTE FALHOU!")
        print("   Verifique os erros acima e corrija as configurações.")
    
    print(f"⏰ Teste executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
