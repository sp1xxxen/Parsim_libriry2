import requests
from urllib.parse import urlsplit, urljoin
import os
from bs4 import BeautifulSoup
from sanitize_filename import sanitize
from pathlib import Path
import time
import json
import argparse


def download_text(url_download, file_name, folder_name="text"):
    os.makedirs(folder_name, exist_ok=True)
    response = requests.get(url_download)
    file_path = os.path.join(folder_name,f"{sanitize(file_name)}.txt")
    with open(file_path, 'w', encoding="UTF-8") as file:
        file.write(response.text)


def download_img(url, folder_name="images"):
    os.makedirs(folder_name, exist_ok=True)
    split = urlsplit(url)
    all_path = os.path.split(split.path)[-1]
    name, extention = os.path.splitext(all_path)
    file_name = f"{name}{extention}"
    file_path = os.path.join(folder_name, file_name)
    response = requests.get(url)
    response.raise_for_status()
    with open(file_path, 'wb') as file:
        file.write(response.content)


def get_info_book(url_book):
    response = requests.get(url_book)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    img_book = soup.find('div', class_="big-book-left-block").find("img")["src"]
    full_img_url = urljoin("https://knigofil.org/", img_book)
    book_title = soup.find('h1', class_ = "big-book-value").text
    book_info = soup.find_all('div', class_ = "big-book-stat")
    all_info_book = []
    for info in book_info:
        if info.find("a") is None:
            continue
        book_info = info.find("a").text
        all_info_book.append(book_info)
    book_author = all_info_book[0]
    book_genre = all_info_book[1]
    book_released = all_info_book[2]
    info_book = {'name': book_title,
    'author_name': book_author,
    'genre': book_genre,
    'year_released': book_released,
    'img_src': f"images/{img_book}",
    'book_path': f"text/{sanitize(book_title)}.txt" }
    return info_book, full_img_url



def get_book_fantasy(url_fantasy):
    response = requests.get(url_fantasy)
    soup = BeautifulSoup(response.text, 'lxml')
    fantasy_books = soup.find('div', class_ = "b-thumbnails")
    fantasy = fantasy_books.find_all('div', class_ = "grid-thumb")
    fantasy_books_url = []
    for book in fantasy:
        fantasy_books_urls = book.find("a")["href"]
        fantasy_books_url.append(fantasy_books_urls)
    return fantasy_books_url


def main():
    urls_books = []
    all_info_books = []
    parser = argparse.ArgumentParser(description="Описание что делает программа")
    parser.add_argument("--start_page", type=int, help="Введите номер начальной страницы", default=1)
    parser.add_argument("--end_page", type=int, help="Введите номер конечной страницы", default=11)
    parser.add_argument("--skip_imgs", help="Пропустить картинки", action="store_true")
    parser.add_argument("--skip_txt", help="Пропустить текст", action="store_true")
    args = parser.parse_args()
    for page_number in range(args.start_page, args.end_page):
        try:
            url_fantasy = f"https://knigofil.org/fantasy/page/{page_number}"
            response = requests.get(url_fantasy)
            soup = BeautifulSoup(response.text, 'lxml')
            new_books = soup.find('div', class_ = "b-thumbnails")
            books = new_books.find_all('div', class_ = "b-thumbnail")
            for book in books:
                url_book = book.find("a")["href"]
                urls_books.append(url_book)
        except requests.exceptions.HTTPError:
            print("Книга не найдена")
        except requests.exceptions.ConnectionError:
            print("Повторное подключение с сервером через 20 секунд")
            time.sleep(20)
    for url_book in urls_books:
        info_book, full_img_url = get_info_book(url_book)
        response = requests.get(url_book)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        download_links = soup.find_all('div', class_="download-link")
        txt_download_link = None
        for link in download_links:
            download_link = link.find('a')["href"]
            file_extention = Path(download_link).suffix
            if file_extention == ".txt":
                txt_download_link = urljoin("https://knigofil.org/", download_link)
                break
        if txt_download_link is None:
            print("Ссылка не найдена")
            continue
        all_info_books.append(info_book)
        print(
    f"""Название книги: {info_book["name"]}
    Имя автора:{info_book["author_name"]}
    Жанр: {info_book["genre"]}
    Год издания: {info_book["year_released"]}""")
        with open('book.json', "w", encoding="UTF-8") as file:
            json.dump(all_info_books, file, ensure_ascii=False)
        print(full_img_url)
        print(txt_download_link)
        if not args.skip_imgs:
            download_img(full_img_url)
        if not args.skip_txt:
            download_text(txt_download_link, info_book["name"])
        

if __name__ == '__main__':
    main()