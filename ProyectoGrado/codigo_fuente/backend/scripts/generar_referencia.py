import argparse
import numpy as np
from ultralytics import YOLO

def generate_reference(video_path, output_file="referencia_armbar.npy"):
    try:
        model = YOLO("yolo26n-pose.pt")
    except Exception:
        print("yolo26n-pose.pt no encontrado, usando yolo11n-pose.pt")
        model = YOLO("yolo11n-pose.pt")
        
    print(f"Extrayendo keypoints de: {video_path}")
    resultados = model.predict(source=video_path, stream=True, verbose=False)
    
    vector = None
    for res in resultados:
        if res.keypoints and len(res.keypoints.data) > 0:
            vector = res.keypoints.data[0].flatten().tolist()
            break  # Tomamos el primer frame válido para el demo
            
    if vector:
        np_vector = np.array(vector)
        np.save(output_file, np_vector)
        print(f"✅ Vector de referencia generado y guardado en {output_file}")
    else:
        print("❌ No se encontraron keypoints en el video.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True, help="Ruta al video de referencia")
    parser.add_argument("--out", type=str, default="referencia_armbar.npy", help="Archivo de salida (.npy)")
    args = parser.parse_args()
    generate_reference(args.video, args.out)
