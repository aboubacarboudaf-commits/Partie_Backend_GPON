import os
from typing import Optional

import requests

ZABBIX_URL = os.getenv("ZABBIX_URL", "").strip()
ZABBIX_USER = os.getenv("ZABBIX_USER", "").strip()
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "").strip()
ZABBIX_API_TOKEN = os.getenv("ZABBIX_API_TOKEN", "").strip()


class ZabbixClient:
    """Client JSON-RPC minimal pour l'API Zabbix (host.get / problem.get).

    Configuré via .env (ZABBIX_URL + soit ZABBIX_API_TOKEN, soit ZABBIX_USER/ZABBIX_PASSWORD).
    Toute erreur réseau/API est avalée (retourne None/[]) pour que l'absence ou
    l'indisponibilité du serveur Zabbix ne casse jamais le reste de l'application.
    """

    def __init__(self, url: str, token: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.url = url.rstrip("/")
        if not self.url.endswith("api_jsonrpc.php"):
            self.url = f"{self.url}/api_jsonrpc.php"
        self._token = token
        self._user = user
        self._password = password
        self._id = 0

    def _call(self, method: str, params: dict) -> Optional[dict]:
        self._id += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": self._id}
        if self._token and method != "user.login":
            payload["auth"] = self._token
        try:
            resp = requests.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json-rpc"},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                print(f"[zabbix] erreur API sur {method}: {data['error']}")
                return None
            return data.get("result")
        except Exception as exc:  # réseau, timeout, JSON invalide, serveur indisponible...
            print(f"[zabbix] appel {method} échoué: {exc}")
            return None

    def _ensure_auth(self) -> bool:
        if self._token:
            return True
        if not self._user or not self._password:
            return False
        result = self._call("user.login", {"username": self._user, "password": self._password})
        if result:
            self._token = result
            return True
        return False

    def get_hosts_by_ip(self, adresses_ip: list) -> dict:
        """Retourne {adresse_ip: {"hostid":..., "available": bool, "status": str}} pour les
        hosts Zabbix dont une interface correspond à une des adresses IP demandées.

        Le mapping équipement ↔ host Zabbix se fait par adresse IP (pas par un identifiant
        saisi manuellement) : dès qu'un équipement a une IP supervisée côté Zabbix, il
        apparaît automatiquement, comme au moment de la config initiale."""
        if not adresses_ip or not self._ensure_auth():
            return {}
        result = self._call(
            "host.get",
            {"output": ["hostid", "status", "available"], "selectInterfaces": ["ip"]},
        )
        if not result:
            return {}
        ip_recherchees = set(adresses_ip)
        mapping = {}
        for h in result:
            for interface in h.get("interfaces") or []:
                ip = interface.get("ip")
                if ip in ip_recherchees:
                    mapping[ip] = {
                        "hostid": h["hostid"],
                        "available": h.get("available") == "1",
                        "status": h.get("status"),
                    }
        return mapping

    def get_active_problems(self, host_ids: list) -> list:
        """Retourne la liste des problèmes actifs (non résolus) pour les hosts demandés."""
        if not host_ids or not self._ensure_auth():
            return []
        result = self._call(
            "problem.get",
            {
                "output": ["eventid", "objectid", "name", "severity", "clock"],
                "selectHosts": ["hostid"],
                "hostids": host_ids,
                "recent": False,
                "sortfield": ["eventid"],
                "sortorder": "DESC",
            },
        )
        return result or []


def get_zabbix_client() -> Optional[ZabbixClient]:
    if not ZABBIX_URL:
        return None
    if not ZABBIX_API_TOKEN and not (ZABBIX_USER and ZABBIX_PASSWORD):
        return None
    return ZabbixClient(ZABBIX_URL, token=ZABBIX_API_TOKEN or None, user=ZABBIX_USER, password=ZABBIX_PASSWORD)
