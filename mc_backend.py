import os
import time
import json

import requests
from dotenv import load_dotenv, find_dotenv

from config import AUCTION


load_dotenv(find_dotenv())


class Auction:
    def __init__(self, api_key, auction_id):
        self._api_key = api_key
        self._auction_id = auction_id

        self.headers = {
            'Authorization': f'{self._api_key}'
        }

        self.check = None

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        self._api_key = value

    @property
    def auction_id(self):
        return self._auction_id

    @api_key.setter
    def auction_id(self, value):
        self._auction_id = value
    
    # Метод, позволяющий получить значение по ключу из кеша
    def get_value(self, key: str, file_name='cache.json'):
        with open(file_name) as file:
            data = file.read()
            json_data = json.loads(data)

        return json_data[key]

    # Метод, в котором мы получаем номер места в аукционе
    def get_position(self):
        self.position = int(input('Введите место, на котором хотите удерживаться:'))

        return self.position

    # Метод, который получает информацию о РК и сохраняет ее в файл 
    def get_aucinfo(self):
        try:
            url = f'https://advert-api.wb.ru/adv/v0/advert?id={self._auction_id}'

            response = requests.get(url, headers=self.headers).json()

            try:

                mc_id = list(response['params'][0].values())[-2]

                data = {
                    'advertId': response['advertId'],
                    'type': response['type'],
                    'status': response['status'],
                    'changeTime': response['changeTime'],
                    'price': response['params'][0]['price'],
                    'Id': mc_id,
                }

                with open('cache.json', 'w') as file:
                    json.dump(data, file)  
                    print('Сохранение файла с данными рк прошло успешно')

            except KeyError:
                print('Синхронизация с бд еще не произошла, повторите попытку позже!!!')

        except ConnectionError:
            print('Соединение потеряно!!!\n<Response [400]>')

    # Метод проверки стоимости места в аукционе
    def check_position(self, position: int):
        url = f"https://advert-api.wb.ru/adv/v0/cpm?type={self.get_value('type')}&param={self.get_value('Id')}"

        response = requests.get(url, headers=self.headers).json()

        value = response[position - 1]['Cpm']
        print(f'Стоимость позиции {position}: {value}')

        return value

    # Вывод списка ставок по местам
    def price_list(self):
        url = f"https://advert-api.wb.ru/adv/v0/cpm?type={self.get_value('type')}&param={self.get_value('Id')}"

        # Переформатировать список в удобный
        response = requests.get(url, headers=self.headers).json()

        return response
    
    # Запустить РК
    def start_mc(self):
        url = f'https://advert-api.wb.ru/adv/v0/start?id={self.get_value("advertId")}'

        response = requests.get(url, headers=self.headers)
        print(response)
        
        if response == '<Response [400]>':
            print('Увеличьте баланс РК!!!')

        else:
            print('РК успешно запущена!')
            
    # Поставить РК на паузу
    def pause_mc(self):
        url = f'https://advert-api.wb.ru/adv/v0/pause?id={self.get_value("advertId")}'

        response = str(requests.get(url, headers=self.headers))

        if response == '<Response [400]>':
            print('Ошибка паузы РК!!!')
        
        else:
            print('РК успешно поставлена на паузу!')
    
    # Метод, который проверяет статус РК
    def check_status(self):
        status = self.get_value('status')
        
        if status == 9:
            self.check = True
            print('РК запущена')

        
        elif status == 11:
            self.check = False
            print('РК на паузе')

        return self.check

    # Изменить ставку в РК
    def change_price(self, price: int):
        url = 'https://advert-api.wb.ru/adv/v0/cpm'

        js_req = {
            "advertId": self.get_value('advertId'),
            "type": self.get_value('type'),
            "cpm": price,
            "param": self.get_value('Id'),
        }

        req = requests.post(url, headers=self.headers, json=js_req)
        
        if str(req) == '<Response [200]>':
            print('Изменение цены прошло успешно')
        
        else:
            print('Ошибка изменения цены!!!')
    
    def start(self, position):
        
        self.get_aucinfo()
        
        if self.check_status():
            # Пока временный цикл заглужка
            while True:
                self.get_aucinfo()

                if self.get_value('status') == 9:
                    position_cost = self.check_position(position)

                    if self.get_value('price') == position_cost:
                        time.sleep(32)
                        print('Вы и так на 1 месте')
                        continue
                    
                    elif self.get_value('price') < position_cost:
                        self.change_price(position_cost + 1)
                        time.sleep(32)
                        continue
                
                else:
                    break


def main():
    test = Auction(os.getenv('API_KEY'), AUCTION)
    
    # test.start_mc()
    position = test.get_position()
    test.start(position)
    

if __name__ == '__main__':
    main()
