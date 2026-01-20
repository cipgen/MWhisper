
import sys
import os
import time
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from audio_capture import AudioCapture
    
    # Target Device ID for MacBook Pro Microphone
    TARGET_DEVICE = 2
    
    print(f"Testing Device ID {TARGET_DEVICE}...")
    capture = AudioCapture(device_id=TARGET_DEVICE)
    
    print("Starting recording for 2 seconds...")
    capture.start()
    time.sleep(2)
    audio = capture.stop()
    
    print(f"Recording stopped. Captured {len(audio)} samples.")
    
    if len(audio) > 0:
        max_amp = np.max(np.abs(audio))
        print(f"Max Amplitude: {max_amp}")
        if max_amp == 0:
            print("WARNING: Still Silence!")
        else:
            print("✓ Audio recorded successfully from Device 2")
    else:
        print("ERROR: No audio captured!")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
