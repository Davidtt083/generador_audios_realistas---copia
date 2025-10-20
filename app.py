import os
import struct
import mimetypes
from flask import Flask, render_template, request, url_for, jsonify
from dotenv import load_dotenv
import uuid

env_path = '/home/vocesrealistas/generador_audios_realistas---copia/.env'


import google.generativeai as genai

env_path = '/home/vocesrealistas/generador_audios_realistas---copia/.env'


load_dotenv(dotenv_path=env_path)

app = Flask(__name__)


if not os.path.exists("static"):
    os.makedirs("static")


try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY no encontrada en el archivo .env")

    genai.configure(api_key=api_key)
    print("API Key de Gemini configurada exitosamente.")
except Exception as e:
    print(f"Error crítico al configurar la API Key: {e}")
    
    exit()


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Genera una cabecera de archivo WAV para los datos de audio crudos."""
    
    try:
        sample_rate = int(mime_type.split("rate=")[1])
    except (IndexError, ValueError):
        sample_rate = 24000 
    bits_per_sample = 16
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1,
        num_channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b"data", data_size
    )
    return header + audio_data

# --- RUTAS DE FLASK ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    
    text_to_speak = request.form['text']
    voice_name = request.form['voice']

    if not text_to_speak:
        
        return jsonify({'success': False, 'error': 'Por favor, introduce un texto.'}), 400

    try:
        
        model = genai.GenerativeModel('models/gemini-2.5-flash-preview-tts')

        
        generation_config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": voice_name
                    }
                }
            }
        }

        
        response = model.generate_content(
            contents=[text_to_speak],
            generation_config=generation_config
        )

        
        audio_part = response.parts[0]
        audio_bytes_raw = audio_part.inline_data.data
        audio_mime_type = audio_part.inline_data.mime_type

       
        wav_data = convert_to_wav(audio_bytes_raw, audio_mime_type)

        
        unique_filename = f"{str(uuid.uuid4())}.wav"

        
        static_audio_path = os.path.join("static", unique_filename)
        with open(static_audio_path, "wb") as out:
            out.write(wav_data)
            print(f'Audio content written to file "{static_audio_path}"')

            return jsonify({
            'success': True,
            'audio_file': unique_filename
        })

    except Exception as e:
        print(f"Ocurrió un error durante la síntesis: {e}")
        
        return jsonify({'success': False, 'error': f"Error al generar el audio: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
