# src/core/database_logic.py
import sqlite3
import os
import shutil
from datetime import datetime

class DatabaseConfig:
    # Глобальное состояние настроек
    is_enabled = False
    db_path = ""
    table_name = ""
    datetime_format = "%Y-%m-%d %H:%M:%S"
    
    check_duplicates = False
    custom_note_text = ""
    
    column_order = []  # Хранит порядок ключей для БД
    _backup_done = False  # Флаг создания ежедневного бэкапа

    selected_fields = {
        "title": True,
        "video_url": True,
        "channel_name": True,
        "channel_handle": False,
        "channel_url": False,
        "download_time": True,
        "upload_date": False,
        "duration": False,
        "view_count": False,
        "like_count": False,
        "dislike_count": False,
        "comment_count": False,
        "thumbnail_url": False,
        "description": False,
        "tags": False,
        "resolution": False,
        "fps": False,
        "extension": False,
        "custom_note": False,
        "absolute_path": False,
        "relative_path": False,
        "input_filename": False, 
        "input_quality": False,
        "file_size": False
    }

class DatabaseLogic:
    @staticmethod
    def get_default_db_path():
        out_dir = os.path.abspath(os.path.join(os.getcwd(), "_output"))
        os.makedirs(out_dir, exist_ok=True)
        return os.path.join(out_dir, "database.db")

    @staticmethod
    def get_default_table_name():
        return f"yt_downloads_{datetime.now().strftime('%Y_%m_%d')}"

    @staticmethod
    def save_metadata(info_dict, original_url, params, log_callback=None):
        if not DatabaseConfig.is_enabled:
            return

        db_path = DatabaseConfig.db_path.strip()
        if not db_path:
            db_path = DatabaseLogic.get_default_db_path()

        table_name = DatabaseConfig.table_name.strip()
        if not table_name:
            table_name = DatabaseLogic.get_default_table_name()
            
        table_name = table_name.replace(" ", "_").replace("-", "_")

        # Автоматический Бэкап (Один раз за сессию)
        if not DatabaseConfig._backup_done and os.path.exists(db_path):
            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y_%m_%d')}.db")
            if not os.path.exists(backup_file):
                try:
                    shutil.copy2(db_path, backup_file)
                    if log_callback:
                        log_callback(f"🛡️ Daily DB backup created: {os.path.basename(backup_file)}", replace=False)
                except Exception:
                    pass
            DatabaseConfig._backup_done = True

        # Формируем список столбцов на основе заданного пользователем ПОРЯДКА (column_order)
        order = DatabaseConfig.column_order if DatabaseConfig.column_order else [k for k, v in DatabaseConfig.selected_fields.items() if v]
        
        columns = []
        values = []

        for key in order:
            if not DatabaseConfig.selected_fields.get(key):
                continue
                
            if key == "title":
                columns.append("title")
                values.append(info_dict.get('title', 'Unknown'))
            elif key == "video_url":
                columns.append("video_url")
                values.append(info_dict.get('webpage_url', original_url))
            elif key == "channel_name":
                columns.append("channel_name")
                values.append(info_dict.get('uploader', 'Unknown'))
            elif key == "channel_handle":
                columns.append("channel_handle")
                values.append(info_dict.get('uploader_id', 'Unknown'))
            elif key == "channel_url":
                columns.append("channel_url")
                # Извлекаем ИМЕННО прямую ссылку на канал (по ID, не по handle)
                values.append(info_dict.get('channel_url', 'Unknown'))
            elif key == "duration":
                columns.append("duration_sec")
                values.append(str(info_dict.get('duration', 0)))
            elif key == "view_count":
                columns.append("view_count")
                values.append(str(info_dict.get('view_count', 0)))
            elif key == "like_count":
                columns.append("like_count")
                values.append(str(info_dict.get('like_count', 0)))
            elif key == "dislike_count":
                columns.append("dislike_count")
                values.append(str(info_dict.get('dislike_count', 0)))
            elif key == "comment_count":
                columns.append("comment_count")
                values.append(str(info_dict.get('comment_count', 0)))
            elif key == "upload_date":
                columns.append("upload_date")
                values.append(info_dict.get('upload_date', 'Unknown'))
            elif key == "thumbnail_url":
                columns.append("thumbnail_url")
                values.append(info_dict.get('thumbnail', 'Unknown'))
            elif key == "description":
                columns.append("description")
                values.append(info_dict.get('description', ''))
            elif key == "tags":
                columns.append("tags")
                tags_list = info_dict.get('tags') or []
                values.append(", ".join(tags_list))
            elif key == "resolution":
                columns.append("resolution")
                res_val = info_dict.get('resolution')
                if not res_val:
                    res_val = f"{info_dict.get('width', '')}x{info_dict.get('height', '')}"
                values.append(res_val)
            elif key == "fps":
                columns.append("fps")
                values.append(str(info_dict.get('fps', 0)))
            elif key == "extension":
                columns.append("extension")
                values.append(info_dict.get('ext', 'Unknown'))
            elif key == "download_time":
                columns.append("download_time")
                try:
                    dt_str = datetime.now().strftime(DatabaseConfig.datetime_format)
                except Exception:
                    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                values.append(dt_str)
            elif key == "custom_note":
                columns.append("custom_note")
                values.append(DatabaseConfig.custom_note_text)
            elif key == "absolute_path":
                columns.append("absolute_path")
                req_dl = info_dict.get('requested_downloads')
                filepath = req_dl[0].get('filepath') if req_dl else info_dict.get('_filename', 'Unknown')
                values.append(os.path.abspath(filepath) if filepath and filepath != 'Unknown' else 'Unknown')
            elif key == "relative_path":
                columns.append("relative_path")
                req_dl = info_dict.get('requested_downloads')
                filepath = req_dl[0].get('filepath') if req_dl else info_dict.get('_filename', 'Unknown')
                if filepath and filepath != 'Unknown':
                    try:
                        filepath = os.path.relpath(filepath, os.getcwd())
                    except ValueError:
                        pass # Оставляем абсолютным, если файлы на разных дисках
                values.append(filepath if filepath else 'Unknown')
            elif key == "input_filename":
                columns.append("input_filename")
                fname = params.get('filename', '').strip()
                values.append(fname if fname else info_dict.get('title', 'Unknown'))
            elif key == "input_quality":
                columns.append("input_quality")
                quality = params.get('quality', '')
                if params.get('mode') == 'audio':
                    quality = "audio"  
                values.append(quality)
            elif key == "file_size":
                columns.append("file_size")
                req_dl = info_dict.get('requested_downloads')
                filepath = req_dl[0].get('filepath') if req_dl else info_dict.get('_filename')
                
                # Пытаемся получить точный вес с диска
                if filepath and os.path.exists(filepath):
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    values.append(f"{size_mb:.2f} MB")
                else:
                    # Если файла нет (например, не скачался), берем оценку от yt-dlp
                    f_size = info_dict.get('filesize') or info_dict.get('filesize_approx')
                    if f_size:
                        values.append(f"{f_size / (1024 * 1024):.2f} MB")
                    else:
                        values.append("Unknown")
            
        if not columns:
            if log_callback: log_callback("⚠️ DB logging is ON, but no fields are selected.", replace=False)
            return

        # Работа с базой данных
        try:
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Создаем каркас таблицы (только ID)
            create_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT)"
            cursor.execute(create_query)

            # Умное добавление столбцов
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            for col in columns:
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")

            # Проверка дубликатов (если галочка включена)
            if DatabaseConfig.check_duplicates and "video_url" in columns:
                video_url = info_dict.get('webpage_url', original_url)
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE video_url = ?", (video_url,))
                if cursor.fetchone()[0] > 0:
                    if log_callback: log_callback(f"⚠️ Duplicate found in DB: {video_url}. Skipping DB insert.", replace=False)
                    conn.close()
                    return

            # Вставка данных
            placeholders = ", ".join(["?" for _ in columns])
            insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(insert_query, tuple(values))

            conn.commit()
            conn.close()

            if log_callback:
                log_callback(f"💾 Metadata saved to DB: [{os.path.basename(db_path)}] -> Table [{table_name}]", replace=False)

        except Exception as e:
            if log_callback:
                log_callback(f"❌ Database Error: {e}", replace=False)