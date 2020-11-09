import csv
from logger import logger
import requests
from bs4 import BeautifulSoup
import sys
import re
import os
import pdfkit

CSV_PATH = r'D:\Project\declaration_parser\Список - декларации.csv'
FINAL_DATA_PATH = r'D:\Project\declaration_parser\final_data'
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0'}


def get_csv_data(csv_path):
    logger.info('Загрузка исходных данных из {}'.format(CSV_PATH))
    data = []
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            data.append({'name': row[0], 'url': row[1]})
    return data


def parse_declaration_data(response_str):
    soup = BeautifulSoup(response_str, 'lxml')
    results_blocks = soup.select('.result-container')
    data = []
    for result_block in results_blocks:
        main_block = result_block.select_one('.col-xs-8')
        url_declaration = 'https://public.nazk.gov.ua' + main_block.select_one('h1').select_one('a')['href']
        date = main_block.select('a')[1].text.replace('Дата публікації: ', '').replace(':', '-')
        declaration_name = main_block.select('a')[2].text
        if len(main_block.select('a')) > 3:
            position = main_block.select('a')[3].text.replace('Посада: ', '')
        else:
            position = ''
        data.append({'url': url_declaration, 'date': date, 'name': declaration_name, 'position': position})
    return data


def get_max_page(response_str):
    soup = BeautifulSoup(response_str, 'lxml')
    pagination = soup.select_one('#table-pagination')
    try:
        nums = pagination.select('li')
    except AttributeError:
        save_page(response_str)
        sys.exit()
    if not nums:
        return 1
    else:
        return int(pagination.select('a')[-1]['data-page'])


def get_year(response_str):
    soup = BeautifulSoup(response_str, 'lxml')
    date_block = soup.select_one('.year-dates')
    if not date_block:
        return ''
    else:
        return date_block.select_one('.border.block').text


def main():
    initial_data = get_csv_data(CSV_PATH)
    for el in initial_data:
        logger.info('Получение деклараций {}'.format(el['name']))
        response = requests.get(el['url'], headers=HEADERS)
        max_page = get_max_page(response.text)
        if not max_page:
            logger.info('У {} нету деклараций'.format(el['name']))
            continue
        page = 0
        declaration_data = []
        while page != max_page:
            page += 1
            if page == 1:
                declaration_data_page = parse_declaration_data(response.text)
            else:
                url_page = re.sub('page=(\d+)&q', 'page={}&q'.format(page), el['url'])
                response_page = requests.get(url_page, headers=HEADERS)
                declaration_data_page = parse_declaration_data(response_page.text)
            declaration_data.extend(declaration_data_page)
        for declaration in declaration_data:
            file_path = FINAL_DATA_PATH + '\\{}'.format(el['name'])
            if el['name'] not in os.listdir(FINAL_DATA_PATH):
                os.mkdir(file_path)
            response_declaration = requests.get(declaration['url'], headers=HEADERS)
            year = get_year(response_declaration.text)
            file_name = file_path + '\\{} {} {} {} {}.pdf'.format(declaration['date'],
                                                                  el['name'],
                                                                  year,
                                                                  declaration['name'],
                                                                  declaration['position'])
            logger.info('Сохранение файла {}'.format(file_name))
            pdfkit.from_url(declaration['url'], file_name, configuration=config)


def save_page(respnse_str, file_name='page.html'):
    with open(file_name, 'w', encoding='utf-8') as html_file:
        html_file.write(respnse_str)


if __name__ == '__main__':
    main()
