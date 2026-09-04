import cv2
import numpy as np
import time
import json
import urllib.request
import os
import torch
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from moviepy import VideoFileClip
from faster_whisper import WhisperModel
from ultralytics import YOLO
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import concurrent.futures

class VideoAIService:
    def __init__(self):
        print("\n[INFO] Memuat sistem analisis komersial...")
        self.yolo_model = YOLO('yolov8n-pose.pt')
        self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            
        # Summarizer
        print("[INFO] Memuat modul Summarizer...")
        self.tokenizer = AutoTokenizer.from_pretrained("philschmid/bart-large-cnn-samsum")
        self.summarizer_model = AutoModelForSeq2SeqLM.from_pretrained("philschmid/bart-large-cnn-samsum")

        if not os.path.exists('face_landmarker.task'):
            urllib.request.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                "face_landmarker.task"
            )

        base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1
        )
        self.detector_face = vision.FaceLandmarker.create_from_options(options)

    def _process_video_frames(self, video_path: str):
        """Menganalisis frame video untuk pose dan wajah."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        durasi_video = total_frames / fps if total_frames > 0 else 1
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if height >= 1080: res_text = "1080p"
        elif height >= 720: res_text = "720p"
        elif height >= 480: res_text = "480p"
        else: res_text = f"{width}x{height}"
        kualitas_teks = f"Audio & Video Clear ({res_text})"
        
        minutes = int(durasi_video // 60)
        seconds = int(durasi_video % 60)
        durasi_teks = f"{minutes} Menit {seconds} Detik"

        # OPTIMASI: Kurangi target pemrosesan FPS ke 0.5 (1 frame setiap 2 detik)
        target_processing_fps = 0.5
        skip_interval = max(1, int(round(fps / target_processing_fps)))

        frame_index, frame_count, valid_face_frames, total_brightness = 0, 0, 0, 0.0
        gerakan_kepala_counter, gerakan_tubuh_counter = 0, 0
        gerakan_tangan_counter, kontak_mata_fokus_counter = 0, 0
        prev_nose, prev_torso, prev_iris_left, prev_iris_right = None, None, None, None

        while cap.isOpened():
            # Berikan jeda mikro agar Python GIL (Global Interpreter Lock) dilepas sejenak
            # Ini memungkinkan FastAPI melayani request API lain tanpa freeze/hang.
            time.sleep(0.005)

            ret, frame = cap.read()
            if not ret: break

            frame_index += 1
            if frame_index % skip_interval != 0: continue

            # Resize frame untuk mempercepat pemrosesan
            frame = cv2.resize(frame, (320, 240))
            h_frame, w_frame, _ = frame.shape
            frame_count += 1
            total_brightness += np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

            # 1. Deteksi Wajah
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            face_result = self.detector_face.detect(mp_image)

            if face_result.face_landmarks and len(face_result.face_landmarks) > 0:
                valid_face_frames += 1
                face_landmarks = face_result.face_landmarks[0]

                nose = face_landmarks[1]
                nose_x, nose_y = nose.x * w_frame, nose.y * h_frame
                if prev_nose:
                    if 1.0 < abs(nose_x - prev_nose[0]) + abs(nose_y - prev_nose[1]) < 30.0:
                        gerakan_kepala_counter += 1
                prev_nose = (nose_x, nose_y)

                left_iris, right_iris = face_landmarks[468], face_landmarks[473]
                dev_left = abs(left_iris.x - (face_landmarks[133].x + face_landmarks[33].x) / 2)
                dev_right = abs(right_iris.x - (face_landmarks[362].x + face_landmarks[263].x) / 2)
                iris_shift = abs(left_iris.x - prev_iris_left) + abs(right_iris.x - prev_iris_right) if prev_iris_left else 0.0
                
                prev_iris_left, prev_iris_right = left_iris.x, right_iris.x
                if dev_left < 0.003 and dev_right < 0.003 and iris_shift < 0.002:
                    kontak_mata_fokus_counter += 1

            # 2. Deteksi Tubuh
            results = self.yolo_model(frame, verbose=False)
            if results and results[0].keypoints is not None and len(results[0].keypoints.xy) > 0:
                kps = results[0].keypoints.xy[0].cpu().numpy()
                if len(kps) > 10:
                    left_shoulder, right_shoulder = kps[5], kps[6]
                    left_wrist, right_wrist = kps[9], kps[10]

                    if left_shoulder[0] > 0 and right_shoulder[0] > 0:
                        current_torso = ((left_shoulder[0] + right_shoulder[0])/2, (left_shoulder[1] + right_shoulder[1])/2)
                        shoulder_width = abs(left_shoulder[0] - right_shoulder[0])

                        if prev_torso and shoulder_width > 10:
                            if abs(current_torso[0] - prev_torso[0]) + abs(current_torso[1] - prev_torso[1]) <= shoulder_width * 0.03:
                                gerakan_tubuh_counter += 1
                        prev_torso = current_torso

                        if (left_wrist[0] > 0 and left_wrist[1] > (left_shoulder[1] + 30)) or \
                           (right_wrist[0] > 0 and right_wrist[1] > (right_shoulder[1] + 30)):
                            gerakan_tangan_counter += 1
        cap.release()

        return {
            "durasi_video": durasi_video,
            "durasi_teks": durasi_teks,
            "kualitas_teks": kualitas_teks,
            "frame_count": frame_count,
            "valid_face_frames": valid_face_frames,
            "gerakan_kepala_counter": gerakan_kepala_counter,
            "gerakan_tubuh_counter": gerakan_tubuh_counter,
            "gerakan_tangan_counter": gerakan_tangan_counter,
            "kontak_mata_fokus_counter": kontak_mata_fokus_counter,
        }

    def _process_audio(self, video_path: str, pertanyaan_perusahaan: str, durasi_video: float):
        """Mengekstrak dan mentranskripsi audio, lalu merangkum jawaban."""
        audio_path = f"temp_audio_{int(time.time())}_{np.random.randint(1000)}.wav"
        video = VideoFileClip(video_path)
        if video.audio is None:
            return {"status": "INVALID", "pesan": "Video bisu."}

        try:
            video.audio.write_audiofile(audio_path, logger=None)
            segments, _ = self.whisper_model.transcribe(audio_path, beam_size=1)
            full_transcript = " ".join([s.text for s in list(segments)])
            wps = round(len(full_transcript.split()) / durasi_video, 2) if durasi_video > 0 else 0
        except Exception as e:
            return {"status": "INVALID", "pesan": str(e)}
        finally:
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass

        if len(full_transcript.strip().split()) < 10:
            return {"status": "INVALID", "pesan": "Jawaban terlalu singkat."}

        # Heuristic untuk pertanyaan terjawab
        total_pertanyaan = len([q for q in pertanyaan_perusahaan.split('\n') if q.strip()])
        if total_pertanyaan == 0: total_pertanyaan = 5
        word_count = len(full_transcript.split())
        terjawab = min(total_pertanyaan, max(1, int(word_count / 30)))
        status_jawaban_teks = f"{terjawab} dari {total_pertanyaan} Pertanyaan Terjawab"

        # 4. Ringkasan AI
        ringkasan_jawaban = full_transcript
        try:
            if len(full_transcript.split()) > 30:
                inputs = self.tokenizer(full_transcript, return_tensors="pt", max_length=1024, truncation=True)
                summary_ids = self.summarizer_model.generate(inputs["input_ids"], max_length=60, min_length=20)
                ringkasan_jawaban = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        except:
            pass

        return {
            "status": "SUKSES",
            "wps": wps,
            "status_jawaban_teks": status_jawaban_teks,
            "ringkasan_jawaban": ringkasan_jawaban,
        }

    def analisa_video(self, video_path: str, pertanyaan_perusahaan: str) -> dict:
        # Jalankan pemrosesan video dan audio secara paralel (Threading)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_video = executor.submit(self._process_video_frames, video_path)
            # Kita perlu durasi video untuk WPM, ambil dari VideoFileClip sementara
            try:
                clip = VideoFileClip(video_path)
                durasi_video = clip.duration
                clip.close()
            except:
                durasi_video = 1

            future_audio = executor.submit(self._process_audio, video_path, pertanyaan_perusahaan, durasi_video)

            # Tunggu kedua thread selesai
            video_result = future_video.result()
            audio_result = future_audio.result()

        # Validasi Error dari proses audio
        if audio_result.get("status") == "INVALID":
            return audio_result

        # Validasi Error dari proses video
        frame_count = video_result["frame_count"]
        valid_face_frames = video_result["valid_face_frames"]
        if frame_count == 0 or (valid_face_frames / frame_count) * 100 < 40.0:
            return {"status": "INVALID", "pesan": "Wajah tidak terdeteksi dengan jelas."}

        # Kalkulasi Skor Akhir
        f = frame_count if frame_count > 0 else 1
        e_persen = round(video_result["kontak_mata_fokus_counter"] / f * 100, 2)
        g_persen = round(video_result["gerakan_tangan_counter"] / f * 100, 2)
        p_persen = round(video_result["gerakan_tubuh_counter"] / f * 100, 2)
        h_persen = round(video_result["gerakan_kepala_counter"] / f * 100, 2)
        
        wps = audio_result["wps"]

        s_total = (1 if (1.5 <= wps <= 3.2) else 0) + \
                  (1 if (30.0 <= e_persen <= 80.0) else 0) + \
                  (1 if (20.0 <= g_persen <= 100.0) else 0) + \
                  (1 if (p_persen > 80.0) else 0) + \
                  (1 if (h_persen > 50.0) else 0)

        if s_total == 5: kategori = "Sangat Baik (High Fit)"
        elif s_total in [3, 4]: kategori = "Baik (Fit)"
        elif s_total == 2: kategori = "Cukup (Moderate Fit)"
        else: kategori = "Kurang (Low Fit)"

        return {
            "status": "SUKSES",
            "kategori_fit": kategori,
            "dimensi_psikologis": {
                "Ability": f"{round(((s_total) / 5) * 100, 2)}%",
                "Intelligent": f"{round(((s_total) / 5) * 100, 2)}%",
                "Personality": f"{round(((s_total) / 5) * 100, 2)}%",
                "Attitude": f"{round(((s_total) / 5) * 100, 2)}%",
                "Emotional Intelligent": f"{round(((s_total) / 5) * 100, 2)}%"
            },
            "ringkasan_jawaban": audio_result["ringkasan_jawaban"],
            "durasi_teks": video_result["durasi_teks"],
            "kualitas_teks": video_result["kualitas_teks"],
            "status_jawaban_teks": audio_result["status_jawaban_teks"]
        }

video_ai_service = VideoAIService()
