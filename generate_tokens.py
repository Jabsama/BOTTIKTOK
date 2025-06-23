#!/usr/bin/env python3
"""
🔑 Générateur automatique de tokens OAuth
Génère les access_token et refresh_token manquants pour TikTok et YouTube
"""

import os
import sys
import json
import time
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class TokenHandler(BaseHTTPRequestHandler):
    """Handler pour capturer les codes OAuth"""
    
    def do_GET(self):
        """Capture le code d'autorisation"""
        if 'code=' in self.path:
            # Extraire le code
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                self.server.auth_code = params['code'][0]
                
                # Réponse de succès
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>✅ Autorisation réussie!</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>🎉 Autorisation réussie!</h1>
                    <p>Tu peux fermer cette fenêtre et retourner au terminal.</p>
                    <p>Le bot va maintenant générer tes tokens automatiquement!</p>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                
                # Arrêter le serveur
                threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Supprimer les logs du serveur"""
        pass

class TokenGenerator:
    """Générateur de tokens OAuth pour TikTok et YouTube"""
    
    def __init__(self):
        self.redirect_uri = "http://localhost:8080/callback"
        
        # Credentials TikTok
        self.tiktok_client_key = os.getenv('TIKTOK_CLIENT_KEY')
        self.tiktok_client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
        
        # Credentials YouTube
        self.youtube_client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.youtube_client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    
    def start_local_server(self):
        """Démarre un serveur local pour capturer le callback OAuth"""
        server = HTTPServer(('localhost', 8080), TokenHandler)
        server.auth_code = None
        
        print(f"🌐 Serveur local démarré sur {self.redirect_uri}")
        server.handle_request()
        
        return server.auth_code
    
    def generate_tiktok_tokens(self):
        """Génère les tokens TikTok via OAuth"""
        print("\n🎵 GÉNÉRATION DES TOKENS TIKTOK")
        print("=" * 50)
        
        if not self.tiktok_client_key or not self.tiktok_client_secret:
            print("❌ Client Key ou Client Secret TikTok manquant!")
            return None, None, None
        
        # URL d'autorisation TikTok
        auth_url = (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={self.tiktok_client_key}"
            f"&scope=user.info.basic,video.list,video.upload"
            f"&response_type=code"
            f"&redirect_uri={urllib.parse.quote(self.redirect_uri)}"
            f"&state=tiktok_auth"
        )
        
        print(f"🔗 Ouverture de l'autorisation TikTok...")
        webbrowser.open(auth_url)
        
        print("⏳ En attente de l'autorisation...")
        auth_code = self.start_local_server()
        
        if not auth_code:
            print("❌ Aucun code d'autorisation reçu!")
            return None, None, None
        
        print(f"✅ Code d'autorisation reçu: {auth_code[:10]}...")
        
        # Échanger le code contre des tokens
        token_url = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
        
        data = {
            'client_key': self.tiktok_client_key,
            'client_secret': self.tiktok_client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, data=data)
            result = response.json()
            
            if result.get('code') == 0:
                access_token = result['data']['access_token']
                refresh_token = result['data']['refresh_token']
                
                # Obtenir l'ID du compte business
                profile_url = "https://business-api.tiktok.com/open_api/v1.3/user/info/"
                headers = {'Access-Token': access_token}
                
                profile_response = requests.get(profile_url, headers=headers)
                profile_data = profile_response.json()
                
                business_id = None
                if profile_data.get('code') == 0:
                    business_id = profile_data['data']['user']['user_id']
                
                print("✅ Tokens TikTok générés avec succès!")
                return access_token, refresh_token, business_id
            else:
                print(f"❌ Erreur TikTok: {result.get('message', 'Erreur inconnue')}")
                return None, None, None
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération des tokens TikTok: {e}")
            return None, None, None
    
    def generate_youtube_tokens(self):
        """Génère les tokens YouTube via OAuth"""
        print("\n📺 GÉNÉRATION DES TOKENS YOUTUBE")
        print("=" * 50)
        
        if not self.youtube_client_id or not self.youtube_client_secret:
            print("❌ Client ID ou Client Secret YouTube manquant!")
            return None
        
        # URL d'autorisation YouTube
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?client_id={self.youtube_client_id}"
            f"&redirect_uri={urllib.parse.quote(self.redirect_uri)}"
            f"&scope=https://www.googleapis.com/auth/youtube.upload"
            f"&response_type=code"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        
        print(f"🔗 Ouverture de l'autorisation YouTube...")
        webbrowser.open(auth_url)
        
        print("⏳ En attente de l'autorisation...")
        auth_code = self.start_local_server()
        
        if not auth_code:
            print("❌ Aucun code d'autorisation reçu!")
            return None
        
        print(f"✅ Code d'autorisation reçu: {auth_code[:10]}...")
        
        # Échanger le code contre des tokens
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': self.youtube_client_id,
            'client_secret': self.youtube_client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, data=data)
            result = response.json()
            
            if 'refresh_token' in result:
                refresh_token = result['refresh_token']
                print("✅ Token YouTube généré avec succès!")
                return refresh_token
            else:
                print(f"❌ Erreur YouTube: {result.get('error_description', 'Erreur inconnue')}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération du token YouTube: {e}")
            return None
    
    def update_env_file(self, tiktok_access, tiktok_refresh, tiktok_business_id, youtube_refresh):
        """Met à jour le fichier .env avec les nouveaux tokens"""
        print("\n💾 MISE À JOUR DU FICHIER .ENV")
        print("=" * 50)
        
        try:
            # Lire le fichier .env actuel
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer les tokens
            if tiktok_access:
                content = content.replace('TIKTOK_ACCESS_TOKEN=your_access_token_here', 
                                        f'TIKTOK_ACCESS_TOKEN={tiktok_access}')
            
            if tiktok_refresh:
                content = content.replace('TIKTOK_REFRESH_TOKEN=your_refresh_token_here', 
                                        f'TIKTOK_REFRESH_TOKEN={tiktok_refresh}')
            
            if tiktok_business_id:
                content = content.replace('TIKTOK_BUSINESS_ACCOUNT_ID=your_business_account_id_here', 
                                        f'TIKTOK_BUSINESS_ACCOUNT_ID={tiktok_business_id}')
            
            if youtube_refresh:
                content = content.replace('YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token_here', 
                                        f'YOUTUBE_REFRESH_TOKEN={youtube_refresh}')
            
            # Sauvegarder le fichier
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fichier .env mis à jour avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du .env: {e}")
    
    def run(self):
        """Lance la génération complète des tokens"""
        print("🚀" + "="*60 + "🚀")
        print("   GÉNÉRATEUR AUTOMATIQUE DE TOKENS OAUTH")
        print("   Génération des tokens manquants pour TikTok et YouTube")
        print("🚀" + "="*60 + "🚀")
        
        # Générer les tokens TikTok
        tiktok_access, tiktok_refresh, tiktok_business_id = self.generate_tiktok_tokens()
        
        # Générer les tokens YouTube
        youtube_refresh = self.generate_youtube_tokens()
        
        # Mettre à jour le fichier .env
        if any([tiktok_access, tiktok_refresh, tiktok_business_id, youtube_refresh]):
            self.update_env_file(tiktok_access, tiktok_refresh, tiktok_business_id, youtube_refresh)
            
            print("\n🎉 GÉNÉRATION TERMINÉE!")
            print("=" * 50)
            print("✅ Tes tokens ont été générés et sauvegardés dans .env")
            print("🚀 Tu peux maintenant lancer ton bot viral:")
            print("   python run_bot.py")
        else:
            print("\n❌ Aucun token n'a pu être généré.")
            print("Vérifie tes credentials dans le fichier .env")

def main():
    """Fonction principale"""
    if not os.path.exists('.env'):
        print("❌ Fichier .env introuvable!")
        print("Assure-toi d'avoir créé ton fichier .env avec tes credentials.")
        sys.exit(1)
    
    generator = TokenGenerator()
    generator.run()

if __name__ == "__main__":
    main()
