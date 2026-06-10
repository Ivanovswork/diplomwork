# 🔧 ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ МИГРАЦИИ EPUB

## Проблема:
При заходе в список книг происходит ошибка, т.к. поле `format` не существует в базе данных для старых записей.

## Решение:

### Вариант 1: Через Django (если Django работает)

```bash
# Перейти в директорию проекта
cd C:\Users\desti\PycharmProjects\dymplom\backend\reading_api

# Активировать виртуальное окружение
C:\Users\desti\PycharmProjects\dymplom\backend\.venv\Scripts\activate.bat

# Применить миграцию
python manage.py migrate books
```

### Вариант 2: Через SQL (если Django не работает)

Если у вас **SQLite** (по умолчанию):

1. Откройте базу данных: `C:\Users\desti\PycharmProjects\dymplom\backend\reading_api\db.sqlite3`
2. Выполните SQL из файла: `books/migrations/add_epub_support.sql`

Или через Python:

```python
import sqlite3

db_path = r'C:\Users\desti\PycharmProjects\dymplom\backend\reading_api\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Добавить колонки
cursor.execute("ALTER TABLE books_book ADD COLUMN format VARCHAR(10) DEFAULT 'pdf'")
cursor.execute("ALTER TABLE books_book ADD COLUMN extracted_text TEXT")

# Обновить существующие записи
cursor.execute("UPDATE books_book SET format = 'pdf' WHERE format IS NULL")

conn.commit()
conn.close()
print("Миграция применена успешно!")
```

### Вариант 3: Вручную через SQLite Browser

1. Скачайте [DB Browser for SQLite](https://sqlitebrowser.org/)
2. Откройте файл `db.sqlite3`
3. Перейдите в вкладку "Execute SQL"
4. Вставьте содержимое `books/migrations/add_epub_support.sql`
5. Нажмите "Execute"

---

## Проверка:

После применения миграции проверьте:

```python
# В Python
import django
django.setup()

from books.models import Book
books = Book.objects.all()
for book in books:
    print(f"{book.name}: format={getattr(book, 'format', 'MISSING')}")
```

Все книги должны показать `format=pdf` (или `epub` если загружены как EPUB).

---

## Если ошибка сохраняется:

1. Проверьте что миграция применена:
```bash
python manage.py showmigrations books
```

Должно быть:
```
books
 [X] 0001_initial
 [X] 0002_book_format_extracted_text
```

2. Если миграция не отмечена, примените её принудительно:
```bash
python manage.py migrate books 0002
```

3. Перезапустите Django сервер:
```bash
python manage.py runserver
```
