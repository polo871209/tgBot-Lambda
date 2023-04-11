import datetime
import time

import requests


class Imperva:

    def __init__(self, api_id: str, api_key: str) -> None:
        self.auth_header = {
            'x-API-Id': api_id,
            'x-API-Key': api_key,
        }

    @staticmethod
    def convert_timestamp(date: str) -> str:
        time_stamp = time.mktime(
            datetime.datetime.strptime(date, '%Y-%m-%d').timetuple())
        return str(round(time_stamp)) + '000'

    def top_sites(
            self,
            account_id: str,
            start_date: str,
            end_date: str,
            count: int = 10,
    ):

        sites_list = []
        domain_list = []
        bandwidth = []
        count = int(count)

        api_url = 'https://my.imperva.com'
        list_sites_endpoint = '/api/prov/v1/sites/list'
        traffic_endpoint = '/api/stats/v1'

        start_datestamp = self.convert_timestamp(start_date)
        end_datestamp = self.convert_timestamp(end_date)
        granularity = int(end_datestamp) - int(start_datestamp)

        for page in range(5):
            params = {
                'account_id': account_id,
                'page_size': 100,
                'page_num': str(page)
            }

            response = requests.post(
                f'{api_url}{list_sites_endpoint}',
                params=params,
                headers=self.auth_header
            ).json()

            try:
                for site in response['sites']:
                    domain = site['domain']
                    site_id = str(site['site_id'])
                    sites_list.append(site_id)
                    domain_list.append(f'{domain}({site_id})')

            except (IndexError, ValueError):
                page = 'null'

        for i in range(len(sites_list)):

            params = {
                'site_id': sites_list[i],
                'time_range': 'custom',
                'start': start_datestamp,
                'end': end_datestamp,
                'stats': 'bandwidth_timeseries',
                'granularity': granularity
            }

            response = requests.post(
                f'{api_url}{traffic_endpoint}',
                headers=self.auth_header,
                params=params
            ).json()
            bandwidth_time = response['bandwidth_timeseries'][0]['data']

            if len(bandwidth_time) == 0:
                bandwidth.append(0)
            else:
                bandwidth.append(
                    round(bandwidth_time[0][1] / (1024 ** 3), 2)
                )

        site_bandwidth = dict(zip(domain_list, bandwidth))
        sorted_site_bandwidth = {k: v for k, v in sorted(
            site_bandwidth.items(), key=lambda item: item[1], reverse=True)}
        domain_list, bandwidth = list(sorted_site_bandwidth.keys())[
                                 0:count], list(sorted_site_bandwidth.values())[0:count]
        with open(f'/tmp/{start_date}-{end_date}.csv', 'w') as f:
            f.write('Rank,Site,bandwidth\n')
            for i in range(len(domain_list)):
                f.write(f'TOP{i + 1},{domain_list[i]},{bandwidth[i]} MB\n')
