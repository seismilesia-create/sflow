import sounddevice as sd
import numpy as np
import time

print("=== Dispositivos de audio disponibles ===\n")
print(sd.query_devices())
print(f"\nDispositivo de entrada por defecto: {sd.default.device[0]}")
print(f"Dispositivo de salida por defecto: {sd.default.device[1]}")

default_input = sd.query_devices(sd.default.device[0])
print(f"\nInfo del mic por defecto: {default_input['name']}")
print(f"  Max input channels: {default_input['max_input_channels']}")
print(f"  Default samplerate: {default_input['default_samplerate']}")

print("\n=== Test de grabacion (3 segundos) ===")
print("Habla algo al microfono...")

try:
    recording = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='int16')
    sd.wait()
    amplitude = np.abs(recording).mean()
    max_amp = np.abs(recording).max()
    print(f"\nAmplitud promedio: {amplitude:.1f}")
    print(f"Amplitud maxima:   {max_amp}")

    if max_amp < 50:
        print("\n>>> PROBLEMA: No se detecto audio. El microfono puede estar muteado o no configurado.")
        print("    Revisa: Configuracion de Windows > Sistema > Sonido > Entrada")
    elif max_amp < 500:
        print("\n>>> Audio muy bajo. El microfono funciona pero con volumen muy bajo.")
    else:
        print("\n>>> Microfono OK! Se detecto audio correctamente.")
except Exception as e:
    print(f"\nERROR: {e}")
