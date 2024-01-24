import sqlite3


def sqlite_db():
    # Подключение к базе данных (если базы данных нет, она будет создана)
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()

    # Создание таблицы, если она еще не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teacher (
        id INTEGER PRIMARY KEY,
        name TEXT,
        avatar TEXT,
        username TEXT,
        password TEXT
    )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY,
            name TEXT,
            class_id INTEGER,
            avatar TEXT,
            username TEXT,
            password TEXT,
            FOREIGN KEY (class_id) REFERENCES class_list(id)
        )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_list (
                id INTEGER PRIMARY KEY,
                title TEXT,
                teacher_id INTEGER,
                FOREIGN KEY (teacher_id) REFERENCES teacher(id)
            )
            ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons_list (
                id INTEGER PRIMARY KEY,
                class_id INTEGER,
                title TEXT,
                matching_game INTEGER,
                contents_offer INTEGER,
                say_the_word INTEGER,
                poem BOOLEAN,
                reading BOOLEAN,
                date_lesson TEXT,
                available BOOLEAN,
                FOREIGN KEY (class_id) REFERENCES class_list(id)
            )
            ''')

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS lesson_word (
                    id INTEGER PRIMARY KEY,
                    lesson_id INTEGER,
                    word TEXT,
                    FOREIGN KEY (lesson_id) REFERENCES lessons_list(id)
                )
                ''')

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lesson_sentences (
                        id INTEGER PRIMARY KEY,
                        lesson_id INTEGER,
                        sentences TEXT,
                        FOREIGN KEY (lesson_id) REFERENCES lessons_list(id)
                    )
                    ''')

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lesson_poem (
                        id INTEGER PRIMARY KEY,
                        lesson_id INTEGER,
                        double_line TEXT,
                        audioURL TEXT,
                        FOREIGN KEY (lesson_id) REFERENCES lessons_list(id)
                    )
                    ''')

    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS lesson_text (
                            id INTEGER PRIMARY KEY,
                            lesson_id INTEGER,
                            line TEXT,
                            startTime FLOAT,
                            endTime FLOAT,
                            audioURL TEXT,
                            FOREIGN KEY (lesson_id) REFERENCES lessons_list(id)
                        )
                        ''')

    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS solving_result (
                            id INTEGER PRIMARY KEY,
                            lesson_id INTEGER,
                            student_id INTEGER
                            job_type TEXT,
                            date_solving TEXT,
                            correspondenceResult INTEGER,
                            sentenceResult INTEGER,
                            speakingResult INTEGER,
                            results BOOLEAN,
                            FOREIGN KEY (lesson_id) REFERENCES lessons_list(id)
                            FOREIGN KEY (student_id) REFERENCES student(id)
                        )
                        ''')

    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS words_data (
                            word TEXT PRIMARY KEY,
                            audio TEXT,
                            image TEXT,
                            status INTEGER
                        )
                        ''')
    # Фиксация изменений и закрытие соединения
    conn.commit()
    conn.close()



if __name__ == '__main__':
    sqlite_db()