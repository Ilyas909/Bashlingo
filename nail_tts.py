#!/usr/bin/env python3
import argparse
import json
import logging
import math
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime
from typing import Dict, Iterable, List, Mapping, Optional

from numbers_util import transcript_number_from_raw_text
from wavfile import write as write_wav

_LOGGER = logging.getLogger("piper_train.infer_onnx")


sess_options = onnxruntime.SessionOptions()
# sess_options.intra_op_num_threads = 3
_LOGGER.debug("Loading model from %s", 'model/step_315496.onnx')
model = onnxruntime.InferenceSession('model/step_315496.onnx',
                                     sess_options=sess_options)

bak_phoneme_ids = {
    "_": [0],
    "^": [1],
    "$": [2],
    " ": [3],
    "!": [4],
    ",": [5],
    "-": [6],
    ".": [7],
    "?": [8],
    "а": [9],
    "б": [10],
    "в": [11],
    "г": [12],
    "д": [13],
    "ж": [14],
    "з": [15],
    "и": [16],
    "i": [17],  # й хәрефе ике символ була, шуға ошоға алыштырам
    "к": [18],
    "л": [19],
    "м": [20],
    "н": [21],
    "о": [22],
    "п": [23],
    "р": [24],
    "с": [25],
    "т": [26],
    "у": [27],
    "ф": [28],
    "х": [29],
    "ц": [30],
    "ч": [31],
    "ш": [32],
    "щ": [33],
    "ы": [34],
    "э": [35],
    "ғ": [36],
    "ҙ": [37],
    "ҡ": [38],
    "ң": [39],
    "ҫ": [40],
    "ү": [41],
    "һ": [42],
    "ә": [43],
    "ө": [44],
    "u": [45],
    "\u0301": [46],  # combining acute accent
    "\u0306": [47],  # combining breve
    "\u0308": [48],  # combining diaeresis
    "—": [49],  # em dash
}


def text_preprocess(text):
    text = text.lower().strip()
    if len(text) == 0:
        return ""
    text = transcript_number_from_raw_text(text)
    text = text.replace('я', 'йа').replace('ю', 'йу').replace('ё',
                                                              'йо').replace('ъ',
                                                                            "").replace(
        'ь', "")

    words = text.replace("-", " ").split(" ")
    words = list(filter(None, words))

    new_words = []
    for word in words:
        new_word = word
        if new_word[0] == "е":
            new_word = 'йэ' + new_word[1:]
        if "е" in word:
            new_word = new_word.replace("е", "э")
        new_words.append(new_word)
    text = " ".join(new_words)
    vowels = ['а', 'ә', 'и', 'ө', 'ы', 'э']
    for c in vowels:
        text = text.replace(f"у{c}", f"u{c}")
        text = text.replace(f"{c}у", f"{c}u")
    text = text.replace(f"й", f"i")

    allowed_chars = set(char for chars in bak_phoneme_ids.keys() for char in chars)
    text = ''.join(char for char in text if char in allowed_chars)


    return text


def phonemes_to_ids(
        phonemes: Iterable[str],
        missing_phonemes: "Optional[Counter[str]]" = None,
        pad: Optional[str] = "_",
        bos: Optional[str] = "^",
        eos: Optional[str] = "$",
) -> List[int]:
    phoneme_id_map = bak_phoneme_ids

    phoneme_ids: List[int] = []

    if bos:
        phoneme_ids.extend(phoneme_id_map[bos])

    if pad:
        phoneme_ids.extend(phoneme_id_map[pad])

    for phoneme in phonemes:
        mapped_phoneme_ids = phoneme_id_map.get(phoneme)
        if mapped_phoneme_ids:
            phoneme_ids.extend(mapped_phoneme_ids)

            if pad:
                phoneme_ids.extend(phoneme_id_map[pad])
        elif missing_phonemes is not None:
            # Make note of missing phonemes
            missing_phonemes[phoneme] += 1

    if eos:
        phoneme_ids.extend(phoneme_id_map[eos])

    return phoneme_ids


def audio_float_to_int16(
        audio: np.ndarray, max_wav_value: float = 32767.0
) -> np.ndarray:
    """Normalize audio and convert to int16 range"""
    audio_norm = audio * (max_wav_value / max(0.01, np.max(np.abs(audio))))
    audio_norm = np.clip(audio_norm, -max_wav_value, max_wav_value)
    audio_norm = audio_norm.astype("int16")
    return audio_norm


sample_rate = 24000
noise_scale = 0.667
length_scale = 1.0
noise_scale_w = 0.8


def main(word, URL, name):
    """Main entry point"""
    logging.basicConfig(level=logging.DEBUG)








    #for i, line in enumerate(sys.stdin):
    line = word.strip().lower()

    if not line:
        return False

    line = text_preprocess(line)
    print(line)
    phoneme_ids = phonemes_to_ids(line)
    print(phoneme_ids)

    text = np.expand_dims(np.array(phoneme_ids, dtype=np.int64), 0)

    path = f"{URL}/{name}.wav"
    generate_by_scales(model, text, sample_rate,
                       path, noise_scale, 1, noise_scale_w)

    print("finish")
    return f"{name}.wav"

def generate_by_scales(model, text, sample_rate, output_path, noise_scale,
                       length_scale, noise_scale_w):
    text_lengths = np.array([text.shape[1]], dtype=np.int64)
    scales = np.array(
        [noise_scale, length_scale, noise_scale_w],
        dtype=np.float32,
    )
    sid = None

    start_time = time.perf_counter()
    audio = model.run(
        None,
        {
            "input": text,
            "input_lengths": text_lengths,
            "scales": scales,
            "sid": sid,
        },
    )[0].squeeze((0, 1))
    # audio = denoise(audio, bias_spec, 10)
    audio = audio_float_to_int16(audio.squeeze())
    end_time = time.perf_counter()

    audio_duration_sec = audio.shape[-1] / sample_rate
    infer_sec = end_time - start_time
    real_time_factor = (
        infer_sec / audio_duration_sec if audio_duration_sec > 0 else 0.0
    )

    write_wav(str(output_path), sample_rate, audio)


def denoise(
        audio: np.ndarray, bias_spec: np.ndarray, denoiser_strength: float
) -> np.ndarray:
    audio_spec, audio_angles = transform(audio)

    a = bias_spec.shape[-1]
    b = audio_spec.shape[-1]
    repeats = max(1, math.ceil(b / a))
    bias_spec_repeat = np.repeat(bias_spec, repeats, axis=-1)[..., :b]

    audio_spec_denoised = audio_spec - (bias_spec_repeat * denoiser_strength)
    audio_spec_denoised = np.clip(audio_spec_denoised, a_min=0.0, a_max=None)
    audio_denoised = inverse(audio_spec_denoised, audio_angles)

    return audio_denoised


def stft(x, fft_size, hopsamp):
    """Compute and return the STFT of the supplied time domain signal x.
    Args:
        x (1-dim Numpy array): A time domain signal.
        fft_size (int): FFT size. Should be a power of 2, otherwise DFT will be used.
        hopsamp (int):
    Returns:
        The STFT. The rows are the time slices and columns are the frequency bins.
    """
    window = np.hanning(fft_size)
    fft_size = int(fft_size)
    hopsamp = int(hopsamp)
    return np.array(
        [
            np.fft.rfft(window * x[i: i + fft_size])
            for i in range(0, len(x) - fft_size, hopsamp)
        ]
    )


def istft(X, fft_size, hopsamp):
    """Invert a STFT into a time domain signal.
    Args:
        X (2-dim Numpy array): Input spectrogram. The rows are the time slices and columns are the frequency bins.
        fft_size (int):
        hopsamp (int): The hop size, in samples.
    Returns:
        The inverse STFT.
    """
    fft_size = int(fft_size)
    hopsamp = int(hopsamp)
    window = np.hanning(fft_size)
    time_slices = X.shape[0]
    len_samples = int(time_slices * hopsamp + fft_size)
    x = np.zeros(len_samples)
    for n, i in enumerate(range(0, len(x) - fft_size, hopsamp)):
        x[i: i + fft_size] += window * np.real(np.fft.irfft(X[n]))
    return x


def inverse(magnitude, phase):
    recombine_magnitude_phase = np.concatenate(
        [magnitude * np.cos(phase), magnitude * np.sin(phase)], axis=1
    )

    x_org = recombine_magnitude_phase
    n_b, n_f, n_t = x_org.shape  # pylint: disable=unpacking-non-sequence
    x = np.empty([n_b, n_f // 2, n_t], dtype=np.complex64)
    x.real = x_org[:, : n_f // 2]
    x.imag = x_org[:, n_f // 2:]
    inverse_transform = []
    for y in x:
        y_ = istft(y.T, fft_size=1024, hopsamp=256)
        inverse_transform.append(y_[None, :])

    inverse_transform = np.concatenate(inverse_transform, 0)

    return inverse_transform


def transform(input_data):
    x = input_data
    real_part = []
    imag_part = []
    for y in x:
        y_ = stft(y, fft_size=1024, hopsamp=256).T
        real_part.append(
            y_.real[None, :, :])  # pylint: disable=unsubscriptable-object
        imag_part.append(
            y_.imag[None, :, :])  # pylint: disable=unsubscriptable-object
    real_part = np.concatenate(real_part, 0)
    imag_part = np.concatenate(imag_part, 0)

    magnitude = np.sqrt(real_part ** 2 + imag_part ** 2)
    phase = np.arctan2(imag_part.data, real_part.data)

    return magnitude, phase


if __name__ == "__main__":
    word = 'Быҙау әйтә: «Мө-мө-мө,       Инәй, эшең бөттөмө?'
    URL = 'static/audio_poem'
    name = 'new'
    main(word, URL, name)
