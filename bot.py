from curl_cffi import requests
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, time, json, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class NaorisProtocol:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://naorisprotocol.network",
            "Referer": "https://naorisprotocol.network/",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    async def user_login(self, address: str, proxy=None, retries=5):
        url = "https://naorisprotocol.network/sec-api/auth/generateToken"
        data = json.dumps({"wallet_address": address})
        
        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    requests.post, url=url, headers=self.headers, data=data, proxy=proxy, timeout=60, impersonate="chrome"
                )
                
                print(f"Response Code: {response.status_code}, Response Text: {response.text}")
                
                if response.status_code == 403:
                    self.print_message(address, proxy, Fore.RED, "403 Forbidden: Possible IP Ban or Wallet Not Whitelisted")
                    return None
                
                if response.status_code == 404:
                    self.print_message(address, proxy, Fore.RED, "Access Token Failed: Join Testnet & Complete Tasks")
                    return None
                
                if response.status_code == 401:
                    self.print_message(address, proxy, Fore.RED, "Unauthorized: Check Wallet Address")
                    return None
                
                response.raise_for_status()
                result = response.json()
                token = result.get('token')
                
                if not token:
                    self.print_message(address, proxy, Fore.RED, "Invalid Token Received")
                    return None
                
                return token
            except requests.RequestException as e:
                self.print_message(address, proxy, Fore.RED, f"Request Error: {str(e)}")
            
            if attempt < retries - 1:
                self.print_message(address, proxy, Fore.YELLOW, "Retrying...")
                proxy = self.rotate_proxy_for_account(address)
                await asyncio.sleep(5)
        
        return None

    async def process_get_access_token(self, address: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        token = None
        
        while token is None:
            token = await self.user_login(address, proxy)
            
            if not token:
                self.print_message(address, proxy, Fore.RED, "Failed to Get Token. Trying a new proxy...")
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
                continue
            
            self.print_message(address, proxy, Fore.GREEN, "Access Token Retrieved Successfully")
            return token
