import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests_cache import CachedSession
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(
        soup=soup, tag='section', attrs={'id': 'what-s-new-in-python'}
    )
    div_with_ul = find_tag(
        soup=main_div, tag='div', attrs={'class': 'toctree-wrapper'}
    )
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(soup=section, tag='a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if not response:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup=soup, tag='h1')
        dl = find_tag(soup=soup, tag='dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(
        soup=soup, tag='div', attrs={'class': 'sphinxsidebarwrapper'}
    )
    ul_tags = sidebar.find_all(name='ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)

        if text_match:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''

        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    table_tag = find_tag(
        soup=soup, tag='table', attrs={'class': 'docutils'}
    )
    zip_tag = find_tag(
        soup=table_tag, tag='a', attrs={'href': re.compile(r'.+\.zip$')}
    )
    link = zip_tag['href']
    archive_url = urljoin(downloads_url, link)
    filename = archive_url.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)

    archive_path = downloads_dir / filename
    response = session.get(archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEP_URL)
    if not response:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    tbody_tags = soup.find_all(name='tbody')

    status_links = []
    for tbody_tag in tbody_tags[:-2]:
        tr_tags = tbody_tag.find_all(name='tr')
        for tr_tag in tr_tags:
            abbr = find_tag(soup=tr_tag, tag='abbr')
            a = find_tag(soup=tr_tag, tag='a')
            type_status, href = abbr.text, a['href']
            status_links.append((type_status[1:], href))

    pep_sum = 0
    status_sum = {}
    for status_link in tqdm(status_links):
        pep_sum += 1
        pep_link = urljoin(PEP_URL, status_link[1])
        response = get_response(session, pep_link)
        if not response:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        dl = find_tag(soup=soup, tag='dl')
        abbr = find_tag(soup=dl, tag='abbr')

        if abbr.text in status_sum.keys():
            status_sum[abbr.text] += 1
        else:
            status_sum[abbr.text] = 1

        if abbr.text not in EXPECTED_STATUS[status_link[0]]:
            logging.info(
                f'Несовпадающие статусы: {pep_link}, '
                f'Статус в карточке: {abbr.text}, '
                f'Ожидаемые статусы: {EXPECTED_STATUS[status_link[0]]}'
            )

    results = [('Статус', 'Количество')]
    for status, sum in status_sum.items():
        results.append((status, sum))
    results.append(('Total:', f'{pep_sum}'))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
