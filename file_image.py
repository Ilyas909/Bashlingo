import json
import sqlite3
from json import JSONDecodeError

from bd import convert_wav_to_mp3
from nail_tts import main


def new_data():
    try:
        with open("image.json", "r") as file:
            imageInf = json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        raise JSONDecodeError("config.json not found")
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    for image in imageInf:
        request = cursor.execute('INSERT OR REPLACE INTO words_data (word, image, status) VALUES (?, ?, true)',
                                 (image['word'].upper(), image['image']))
    conn.commit()
    not_audio = cursor.execute('''SELECT word FROM words_data WHERE audio IS NULL;''').fetchall()
    url = 'static/audio_word'
    if not_audio:
        for word in not_audio:
            audio_url = main(word[0].lower(), url, word[0].upper())
            audio_url = convert_wav_to_mp3(audio_url, url)
            cursor.execute('UPDATE words_data SET audio = ? WHERE word = ?;',
                           (audio_url, word[0].upper()))
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    new_data()
