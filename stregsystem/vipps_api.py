from datetime import datetime, timedelta, date
from django.utils.dateparse import parse_datetime

from requests.auth import HTTPBasicAuth
import requests
from pathlib import Path

import json
import logging


class AccountingAPI(object):
    api_endpoint = 'https://api.vipps.no'
    # Saves secret tokens to the file "vipps-tokens.json" right next to this file.
    # Important to use a separate file since the tokens can change and is thus not suitable for django settings.
    tokens_file = (Path(__file__).parent / 'vipps-tokens.json').as_posix()
    tokens_file_backup = (Path(__file__).parent / 'vipps-tokens.json.bak').as_posix()
    tokens = None

    myshop_number = 90601
    logger = logging.getLogger(__name__)

    @classmethod
    def __read_token_storage(cls):
        """
        Reads the token variable from disk
        """
        with open(cls.tokens_file, 'r') as json_file:
            cls.tokens = json.load(json_file)

        if cls.tokens is None:
            cls.logger.error("read token from storage. 'tokens' is None. Reverting to backup tokens")

            with open(cls.tokens_file_backup, 'r') as json_file_backup:
                cls.tokens = json.load(json_file_backup)

    @classmethod
    def __update_token_storage(cls):
        """
        Saves the token variable to disk
        """
        if cls.tokens is None:
            cls.logger.error(f"'tokens' is None. Aborted writing.")
            return

        with open(cls.tokens_file, 'w') as json_file:
            json.dump(cls.tokens, json_file, indent=2)

    @classmethod
    def __refresh_access_token(cls):
        """
        Fetches a new access token using the refresh token.
        :return:
        """
        url = f"{cls.api_endpoint}/miami/v1/token"

        payload = {
            "grant_type": "client_credentials",
        }

        auth = HTTPBasicAuth(cls.tokens['client_id'], cls.tokens['client_secret'])

        response = requests.post(url, data=payload, auth=auth)
        response.raise_for_status()
        json_response = response.json()
        # Calculate when the token expires
        expire_time = datetime.now() + timedelta(seconds=json_response['expires_in'] - 1)
        cls.tokens['access_token_timeout'] = expire_time.isoformat(timespec='milliseconds')
        cls.tokens['access_token'] = json_response['access_token']

    @classmethod
    def __refresh_ledger_id(cls):
        cls.tokens['ledger_id'] = cls.get_ledger_id(cls.myshop_number)

    @classmethod
    def __refresh_expired_token(cls):
        """
        Client side check if the token has expired.
        """
        cls.__read_token_storage()

        if 'access_token_timeout' not in cls.tokens:
            cls.__refresh_access_token()

        expire_time = parse_datetime(cls.tokens['access_token_timeout'])
        if datetime.now() >= expire_time:
            cls.__refresh_access_token()

        if 'ledger_id' not in cls.tokens:
            cls.__refresh_ledger_id()

        cls.__update_token_storage()

    @classmethod
    def get_transactions_historic(cls, transaction_date: date) -> list:
        """
        Fetches historic transactions (only complete days (e.g. not today)) by date.
        :param transaction_date: The date to look up.
        :return: List of transactions on that date.
        """
        cls.__refresh_expired_token()

        ledger_date = transaction_date.strftime('%Y-%m-%d')

        url = f"{cls.api_endpoint}/report/v2/ledgers/{cls.tokens['ledger_id']}/funds/dates/{ledger_date}"

        params = {
            'includeGDPRSensitiveData': "true",
        }
        headers = {
            'authorization': 'Bearer {}'.format(cls.tokens['access_token']),
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()['items']

    @classmethod
    def fetch_report_by_feed(cls, cursor: str):
        url = f"{cls.api_endpoint}/report/v2/ledgers/{cls.tokens['ledger_id']}/funds/feed"

        params = {
            'includeGDPRSensitiveData': "true",
            'cursor': cursor,
        }
        headers = {
            'authorization': "Bearer {}".format(cls.tokens['access_token']),
        }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        return response.json()

    @classmethod
    def get_transactions_latest_feed(cls) -> list:
        """
        Fetches transactions ahead of cursor. Used to fetch very recent transactions.
        Moves the cursor as well.
        :return: All transactions from the current cursor till it's emptied.
        """

        cls.__refresh_expired_token()

        transactions = []
        cursor = cls.tokens.get('cursor', "")

        while True:
            res = cls.fetch_report_by_feed(cursor)
            transactions.extend(res['items'])

            try_later = res['tryLater'] == "true"

            if try_later:
                break

            cursor = res['cursor']

            if len(res['items']) == 0:
                break

        cls.tokens['cursor'] = cursor
        cls.__update_token_storage()
        return transactions

    @classmethod
    def get_ledger_info(cls, myshop_number: int):
        """
        {
            "ledgerId": "123456",
            "currency": "DKK",
            "payoutBankAccount": {
                "scheme": "BBAN:DK",
                "id": "123412341234123412"
            },
            "owner": {
                "scheme": "business:DK:CVR",
                "id": "16427888"
            },
            "settlesForRecipientHandles": [
                "DK:90601"
            ]
        }
        :param myshop_number:
        :return:
        """
        url = f"{cls.api_endpoint}/settlement/v1/ledgers"
        params = {'settlesForRecipientHandles': 'DK:{}'.format(myshop_number)}
        headers = {
            'authorization': 'Bearer {}'.format(cls.tokens['access_token']),
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        ledger_info = response.json()["items"]

        assert len(ledger_info) != 0

        return ledger_info[0]

    @classmethod
    def get_ledger_id(cls, myshop_number: int) -> int:
        return int(cls.get_ledger_info(myshop_number)["ledgerId"])
