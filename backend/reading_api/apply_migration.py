"""
Скрипт для применения миграции EPUB поддержки
Запустите: python apply_migration.py
"""

import sqlite3
import os

# Путь к базе данных (измените если нужно)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

def apply_migration():
    """Применяет миграцию для добавления полей format и extracted_text"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных не найдена: {DB_PATH}")
        return False
    
    print(f"📂 Подключение к базе: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существует ли уже колонка format
        cursor.execute("PRAGMA table_info(books_book)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'format' in columns:
            print("✅ Колонка 'format' уже существует")
        else:
            print("➕ Добавление колонки 'format'...")
            cursor.execute("ALTER TABLE books_book ADD COLUMN format VARCHAR(10) DEFAULT 'pdf'")
            print("✅ Колонка 'format' добавлена")
        
        if 'extracted_text' in columns:
            print("✅ Колонка 'extracted_text' уже существует")
        else:
            print("➕ Добавление колонки 'extracted_text'...")
            cursor.execute("ALTER TABLE books_book ADD COLUMN extracted_text TEXT")
            print("✅ Колонка 'extracted_text' добавлена")
        
        # Обновляем существующие записи
        print("🔄 Обновление существующих записей...")
        cursor.execute("UPDATE books_book SET format = 'pdf' WHERE format IS NULL OR format = ''")
        updated_count = cursor.rowcount
        print(f"✅ Обновлено {updated_count} записей на format='pdf'")
        
        conn.commit()
        conn.close()
        
        print("\n" + "="*50)
        print("🎉 Миграция успешно применена!")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка применения миграции: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = apply_migration()
    if success:
        print("\n✅ Теперь можете запустить Django сервер:")
        print("   python manage.py runserver")
    else:
        print("\n❌ Исправьте ошибки и попробуйте снова")
