"""
Помощник для скачивания клинических рекомендаций

Этот скрипт помогает организовать процесс скачивания документов.
ВАЖНО: Автоматическое скачивание с cr.minzdrav.gov.ru может быть ограничено.
Рекомендуется скачивать документы вручную через браузер.

Usage:
    python backend/scripts/download_helper.py
"""

import csv
import os
from pathlib import Path
from typing import List, Dict

# Путь к проекту
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
METADATA_FILE = DATA_DIR / "documents_metadata.csv"


class DownloadHelper:
    """Помощник для организации скачивания документов"""

    def __init__(self):
        self.documents = self.load_metadata()

    def load_metadata(self) -> List[Dict]:
        """Загрузить метаданные документов из CSV"""
        documents = []
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                documents.append(row)
        return documents

    def get_pending_documents(self) -> List[Dict]:
        """Получить список документов для скачивания"""
        return [doc for doc in self.documents if doc['status'] == 'pending']

    def get_downloaded_documents(self) -> List[Dict]:
        """Получить список скачанных документов"""
        downloaded = []
        for doc in self.documents:
            file_path = RAW_DIR / doc['filename']
            if file_path.exists():
                downloaded.append(doc)
        return downloaded

    def update_status(self, document_id: int, status: str):
        """Обновить статус документа в CSV"""
        # Читаем все документы
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        # Обновляем статус
        for row in rows:
            if row['id'] == str(document_id):
                row['status'] = status
                break

        # Записываем обратно
        with open(METADATA_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def print_statistics(self):
        """Вывести статистику скачивания"""
        total = len(self.documents)
        downloaded = len(self.get_downloaded_documents())
        pending = total - downloaded

        print(f"\n{'='*60}")
        print(f"Статистика скачивания клинических рекомендаций")
        print(f"{'='*60}")
        print(f"Всего документов:      {total}")
        print(f"Скачано:               {downloaded} ({downloaded/total*100:.1f}%)")
        print(f"Осталось скачать:      {pending} ({pending/total*100:.1f}%)")
        print(f"{'='*60}\n")

    def print_pending_list(self, limit: int = 10):
        """Вывести список документов для скачивания"""
        pending = self.get_pending_documents()[:limit]

        print(f"\nСледующие {min(limit, len(pending))} документов для скачивания:\n")
        print(f"{'ID':<5} {'Файл':<45} {'Специальность':<15}")
        print(f"{'-'*70}")

        for doc in pending:
            print(f"{doc['id']:<5} {doc['filename']:<45} {doc['specialty']:<15}")

        print()

    def generate_download_links(self, limit: int = 10):
        """Сгенерировать ссылки для поиска документов"""
        pending = self.get_pending_documents()[:limit]

        print("\nСсылки для поиска документов:\n")

        for doc in pending:
            title = doc['title']

            # Ссылки на возможные источники
            print(f"\n{doc['id']}. {title}")
            print(f"   Файл: {doc['filename']}")
            print(f"   Поиск на cr.minzdrav.gov.ru:")
            print(f"   https://cr.minzdrav.gov.ru/schema/search?q={title.replace(' ', '+')}")
            print(f"   Поиск на diseases.medelement.com:")
            print(f"   https://diseases.medelement.com/search?q={title.replace(' ', '+')}")

    def check_downloaded_files(self):
        """Проверить скачанные файлы и обновить статусы"""
        print("\nПроверка скачанных файлов...")

        updated = 0
        for doc in self.documents:
            file_path = RAW_DIR / doc['filename']

            if file_path.exists() and doc['status'] == 'pending':
                # Файл существует, обновляем статус
                file_size_mb = file_path.stat().st_size / (1024 * 1024)

                print(f"✓ Найден: {doc['filename']} ({file_size_mb:.2f} MB)")

                # Обновляем в CSV
                self.update_status(int(doc['id']), 'downloaded')
                updated += 1

        if updated > 0:
            print(f"\nОбновлено статусов: {updated}")
            # Перезагружаем метаданные
            self.documents = self.load_metadata()
        else:
            print("\nНовых скачанных файлов не найдено.")

    def interactive_mode(self):
        """Интерактивный режим работы"""
        while True:
            print("\n" + "="*60)
            print("Помощник скачивания клинических рекомендаций")
            print("="*60)
            print("1. Показать статистику")
            print("2. Показать список для скачивания (10 шт)")
            print("3. Сгенерировать ссылки для поиска (10 шт)")
            print("4. Проверить скачанные файлы")
            print("5. Отметить документ как скачанный")
            print("0. Выход")
            print("="*60)

            choice = input("\nВыберите действие: ").strip()

            if choice == '1':
                self.print_statistics()
            elif choice == '2':
                self.print_pending_list(limit=10)
            elif choice == '3':
                self.generate_download_links(limit=10)
            elif choice == '4':
                self.check_downloaded_files()
                self.print_statistics()
            elif choice == '5':
                doc_id = input("Введите ID документа: ").strip()
                try:
                    self.update_status(int(doc_id), 'downloaded')
                    print(f"✓ Документ {doc_id} отмечен как скачанный")
                    self.documents = self.load_metadata()
                except ValueError:
                    print("✗ Неверный ID")
            elif choice == '0':
                print("\nДо свидания!")
                break
            else:
                print("\n✗ Неверный выбор")


def main():
    """Главная функция"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║   Помощник скачивания клинических рекомендаций MedBot AI    ║
╚══════════════════════════════════════════════════════════════╝

ВАЖНО:
- Скачивайте документы вручную через браузер
- Сохраняйте PDF файлы в директорию: data/raw/
- Используйте имена файлов из documents_metadata.csv
- После скачивания запустите "Проверить скачанные файлы"

Источники документов:
1. https://cr.minzdrav.gov.ru/
2. https://diseases.medelement.com/
3. https://www.cardio.ru/klinicheskie-rekomendatsii/
    """)

    helper = DownloadHelper()
    helper.interactive_mode()


if __name__ == "__main__":
    main()
