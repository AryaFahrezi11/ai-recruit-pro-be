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
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import concurrent.futures

# ==========================================================
# Modul Pembantu Pemahaman & Analisis Tanya-Jawab Wawancara
# ==========================================================

def _expand_question(q: str) -> str:
    ql = q.lower()
    exp = [q]
    if any(w in ql for w in ["siapa", "perkenal", "tentang diri", "latar belakang", "profil"]):
        exp.append("perkenalkan diri nama saya latar belakang pendidikan keahlian profil")
    if any(w in ql for w in ["projek", "project", "portofolio", "buat", "karya", "aplikasi", "sistem"]):
        exp.append("projek aplikasi website sistem portofolio yang pernah saya buat kerjakan selesaikan")
    if any(w in ql for w in ["mengapa", "kenapa", "alasan", "melamar", "posisi", "tertarik", "motivasi", "tujuan"]):
        exp.append("alasan melamar motivasi tertarik posisi lowongan pekerjaan cocok sesuai kualifikasi")
    return " . ".join(exp)

def _get_question_keywords(q: str) -> list:
    ql = q.lower()
    kws = []
    if any(w in ql for w in ["projek", "project", "portofolio", "karya", "buat apa", "aplikasi apa", "sistem"]):
        kws.extend(["projek", "project", "portofolio", "buat", "karya", "aplikasi", "website", "web", "app", "lima", "tiga", "dua", "selesai", "fitur"])
    elif any(w in ql for w in ["mengapa", "kenapa", "alasan", "melamar", "posisi", "tertarik", "motivasi", "tujuan"]):
        kws.extend(["mengapa", "kenapa", "alasan", "melamar", "posisi", "tertarik", "motivasi", "job des", "cocok", "lowongan", "perusahaan", "pengalaman", "kualifikasi"])
    elif any(w in ql for w in ["siapa", "perkenal", "tentang diri", "latar belakang", "profil"]):
        kws.extend(["siapa", "diri", "perkenal", "nama", "lulusan", "pendidikan", "universitas", "informatika", "developer", "keahlian", "sarjana", "kuliah"])
    else:
        kws.extend([w for w in re.findall(r'\w+', ql) if len(w) > 3])
    return kws

def _summarize_answer_indonesian(q: str, raw_text: str) -> str:
    ql = q.lower()
    tl = raw_text.lower()
    
    # 1. Projek / Portofolio
    if any(w in ql for w in ["projek", "project", "portofolio", "karya", "buat apa", "aplikasi apa", "sistem"]):
        details = []
        m_count = re.search(r'(?:kurang lebih|sekitar|ada)?\s*(\d+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh)\s*(?:projek|project)', raw_text, re.IGNORECASE)
        if m_count:
            details.append(f"telah menyelesaikan sekitar {m_count.group(1)} proyek")
        elif "beberapa" in tl:
            details.append("telah menyelesaikan beberapa proyek")
        else:
            details.append("telah menyelesaikan portofolio proyek")
            
        types = []
        if any(w in tl for w in ["web", "website"]):
            types.append("aplikasi website")
        if any(w in tl for w in ["mobile", "app", "android", "ios"]):
            types.append("aplikasi mobile")
        if types:
            details.append(f"yang mencakup pengembangan {' dan '.join(types)}")
            
        return f"Kandidat memaparkan pengalaman proyeknya, di mana kandidat {', '.join(details)}."

    # 2. Motivasi / Alasan Melamar
    if any(w in ql for w in ["mengapa", "kenapa", "alasan", "melamar", "posisi", "tertarik", "motivasi", "tujuan"]):
        reasons = []
        if any(w in tl for w in ["job des", "jobdesk", "tanggung jawab", "pekerjaan", "pershare", "persyaratan"]):
            reasons.append("deskripsi pekerjaan (job desk) serta persyaratan yang sesuai")
        if any(w in tl for w in ["cocok", "sesuai", "keahlian", "skill", "pengalaman"]):
            reasons.append("keselarasan kualifikasi dan keahlian yang dimiliki")
        if any(w in tl for w in ["kontribusi", "berkembang", "perusahaan", "majukan"]):
            reasons.append("keinginan untuk berkontribusi bagi perkembangan perusahaan")
            
        if reasons:
            return f"Kandidat menyatakan motivasi melamar didasari oleh {', '.join(reasons)}."
        return "Kandidat menyatakan motivasi melamar karena adanya kesesuaian minat kerja dan kualifikasi dengan posisi yang ditawarkan."

    # 3. Perkenalan Diri / Siapa Kamu / Latar Belakang
    if any(w in ql for w in ["siapa", "perkenal", "tentang diri", "latar belakang", "profil"]):
        points = []
        if any(w in tl for w in ["universitas", "politeknik", "institut", "sekolah", "kampus", "lulusan"]):
            m_inst = re.search(r'(?:dari|di)\s+((?:universitas|politeknik|institut|sekolah|kampus)\s+[A-Za-z\s]+?)(?:\.|\,|$|program|jurusan|prodi)', raw_text, re.IGNORECASE)
            if m_inst:
                points.append(f"lulusan/mahasiswa dari {m_inst.group(1).strip()}")
        if any(w in tl for w in ["informatika", "komputer", "sistem informasi", "teknik"]):
            points.append("bidang studi Teknik Informatika/Komputer")
        if any(w in tl for w in ["developer", "programmer", "engineer", "designer", "stack"]):
            m_pos = re.search(r'(?:posisi|sebagai|bidang)\s+([A-Za-z\s]+?(?:developer|engineer|programmer|designer))', raw_text, re.IGNORECASE)
            pos = m_pos.group(1).strip() if m_pos else "Full Stack Developer"
            points.append(f"dengan fokus keahlian sebagai {pos}")
            
        if points:
            return f"Kandidat memperkenalkan diri ({', '.join(points)})."
        return "Kandidat memperkenalkan latar belakang pendidikan dan fokus keahlian profesional yang dimilikinya."

    # 4. Pertanyaan Umum / Lainnya
    clean_snippet = re.sub(r'\s+', ' ', raw_text).strip()
    if len(clean_snippet) > 140:
        clean_snippet = clean_snippet[:140] + "..."
    return f"Kandidat menanggapi pertanyaan dengan memaparkan: \"{clean_snippet}\"."

def _generate_executive_summary(pertanyaan_results: list, terjawab_count: int, total_pertanyaan: int) -> str:
    paragraphs = []
    if terjawab_count == total_pertanyaan:
        intro = f"Kandidat telah menyelesaikan sesi wawancara video dengan sangat baik dan menjawab seluruh {total_pertanyaan} pertanyaan yang diajukan secara terstruktur."
    elif terjawab_count > 0:
        intro = f"Kandidat telah menyelesaikan sesi wawancara video dengan merespon {terjawab_count} dari {total_pertanyaan} pertanyaan yang diajukan."
    else:
        intro = "Kandidat telah mengunggah rekaman wawancara, namun respon suara verbal belum terdeteksi secara optimal terhadap pertanyaan yang diajukan."
    paragraphs.append(intro)
    
    poin_jawaban = []
    for item in pertanyaan_results:
        if item["status"] in ["Terjawab", "Terjawab Sebagian"] and item.get("ringkasan"):
            poin_jawaban.append(f"• {item['pertanyaan']}: {item['ringkasan']}")
            
    if poin_jawaban:
        paragraphs.append("\n".join(poin_jawaban))
        
    if terjawab_count >= total_pertanyaan:
        conclusion = "Secara menyeluruh, kandidat menunjukkan artikulasi komunikasi yang jelas, relevansi kualifikasi yang kuat dengan deskripsi pekerjaan, serta kesiapan profesional untuk posisi ini."
    else:
        conclusion = "Disarankan untuk melakukan peninjauan lebih lanjut pada aspek pertanyaan yang belum terjawab secara lengkap saat tahapan validasi lanjutan."
    paragraphs.append(conclusion)
    
    return "\n\n".join(paragraphs)

# ==========================================================
# Video AI Service Class
# ==========================================================

class VideoAIService:
    def __init__(self):
        print("\n[INFO] Memuat sistem analisis komersial...")
        self.yolo_model = YOLO('yolov8n-pose.pt')
        self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            
        # Model Pemahaman Semantik Pertanyaan Wawancara (SBERT Multilingual)
        print("[INFO] Memuat modul SBERT Multilingual untuk analisis tanya-jawab wawancara...")
        self.sentence_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

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

    def _process_video_frames(self, video_path: str, progress_callback=None):
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
            time.sleep(0.005)

            ret, frame = cap.read()
            if not ret: break

            frame_index += 1
            if frame_index % skip_interval != 0: continue

            frame = cv2.resize(frame, (640, 480))
            h_frame, w_frame, _ = frame.shape
            frame_count += 1
            total_brightness += np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            if progress_callback and total_frames > 0 and frame_index % (skip_interval * 2) == 0:
                calc_pct = 10 + int((frame_index / total_frames) * 50)
                progress_callback(min(60, calc_pct), f"Menganalisis visual & gestur kandidat ({calc_pct}%)...")

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

    def _process_audio(self, video_path: str, pertanyaan_perusahaan: str, durasi_video: float, pertanyaan_list: list = None, progress_callback=None):
        """Mengekstrak dan mentranskripsi audio, lalu memetakan jawaban ke setiap pertanyaan secara semantik."""
        try:
            video = VideoFileClip(video_path)
            has_audio = video.audio is not None
        except Exception:
            video = None
            has_audio = False

        segments_list = []
        full_transcript = ""
        wps = 0.0

        if not has_audio:
            full_transcript = "(Video tidak memiliki trek audio)"
            if video:
                try: video.close()
                except: pass
        else:
            audio_path = f"temp_audio_{int(time.time())}_{np.random.randint(1000)}.wav"
            try:
                video.audio.write_audiofile(audio_path, logger=None)
                if progress_callback:
                    progress_callback(65, "Mentranskripsi suara wawancara (Whisper AI)...")
                segments, _ = self.whisper_model.transcribe(audio_path, beam_size=1)
                for s in segments:
                    clean_t = s.text.strip()
                    if clean_t:
                        segments_list.append({
                            "start": round(s.start, 2),
                            "end": round(s.end, 2),
                            "text": clean_t
                        })
                full_transcript = " ".join([s["text"] for s in segments_list])
                wps = round(len(full_transcript.split()) / durasi_video, 2) if durasi_video > 0 else 0
            except Exception as e:
                full_transcript = f"(Gagal memproses audio: {str(e)})"
                wps = 0.0
            finally:
                if os.path.exists(audio_path):
                    try: os.remove(audio_path)
                    except: pass
                if video:
                    try: video.close()
                    except: pass

        if not full_transcript.strip() or full_transcript.startswith("("):
            wps = 0.0

        # Siapkan daftar pertanyaan
        questions = []
        if pertanyaan_list and isinstance(pertanyaan_list, list):
            questions = [str(q).strip() for q in pertanyaan_list if str(q).strip()]
        if not questions and pertanyaan_perusahaan:
            questions = [q.strip() for q in pertanyaan_perusahaan.split('\n') if q.strip()]
        if not questions:
            questions = [
                "Ceritakan siapa Anda dan latar belakang pendidikan/keahlian?",
                "Proyek apa saja yang pernah Anda buat atau kerjakan?",
                "Mengapa Anda memutuskan untuk melamar di posisi ini?"
            ]

        total_pertanyaan = len(questions)
        N = len(segments_list)
        K = total_pertanyaan

        # Jika tidak ada suara atau segmen
        if N == 0:
            analisis = []
            for idx, q in enumerate(questions):
                analisis.append({
                    "nomor": idx + 1,
                    "pertanyaan": q,
                    "status": "Tidak Terjawab",
                    "skor_relevansi": 0,
                    "waktu_mulai": 0.0,
                    "waktu_selesai": 0.0,
                    "ringkasan": "Kandidat tidak memberikan respon suara yang terdeteksi.",
                    "kutipan": ""
                })
            return {
                "status": "SUKSES",
                "wps": 0.0,
                "status_jawaban_teks": f"0 dari {total_pertanyaan} Pertanyaan Terjawab",
                "ringkasan_jawaban": "Tidak ada respon suara kandidat yang terdeteksi dalam rekaman wawancara.",
                "analisis_pertanyaan": analisis,
                "pertanyaan_terjawab_count": 0,
                "total_pertanyaan": total_pertanyaan,
                "full_transcript": full_transcript
            }

        if progress_callback:
            progress_callback(80, "Menganalisis kesesuaian semantik jawaban tiap soal (SBERT)...")

        # Encode pertanyaan dan segmen audio dengan model SBERT
        expanded_questions = [_expand_question(q) for q in questions]
        q_embs = self.sentence_model.encode(expanded_questions)
        s_embs = self.sentence_model.encode([s["text"] for s in segments_list])

        sims = cosine_similarity(s_embs, q_embs)
        for i in range(N):
            text_lower = segments_list[i]["text"].lower()
            for k in range(K):
                kws = _get_question_keywords(questions[k])
                match_count = sum(1 for kw in kws if kw in text_lower)
                sims[i][k] += match_count * 0.15

        # Dynamic Programming untuk Partisi Monotonik Sekuensial (Wawancara Berurutan)
        dp = np.full((K + 1, N + 1), -1e9)
        parent = np.zeros((K + 1, N + 1), dtype=int)
        dp[0][0] = 0

        for k in range(1, K + 1):
            for i in range(k, N + 1):
                for j in range(k - 1, i):
                    seg_score = sum(sims[idx][k - 1] for idx in range(j, i))
                    val = dp[k - 1][j] + seg_score
                    if val > dp[k][i]:
                        dp[k][i] = val
                        parent[k][i] = j

        boundaries = [N]
        curr = N
        for k in range(K, 0, -1):
            curr = parent[k][curr]
            boundaries.append(curr)
        boundaries.reverse()

        pertanyaan_results = []
        terjawab_count = 0

        for k in range(K):
            b_start, b_end = boundaries[k], boundaries[k + 1]
            assigned = segments_list[b_start:b_end]
            raw_text = " ".join([s["text"] for s in assigned]).strip()
            
            t_start = assigned[0]["start"] if assigned else 0.0
            t_end = assigned[-1]["end"] if assigned else 0.0
            avg_sim = float(np.mean([sims[idx][k] for idx in range(b_start, b_end)])) if b_start < b_end else 0.0

            if not raw_text or len(raw_text.split()) < 4:
                status = "Tidak Terjawab"
                skor = 0
                ringkasan = "Kandidat tidak memberikan jawaban yang terdeteksi untuk pertanyaan ini."
            else:
                word_count = len(raw_text.split())
                if word_count >= 8 or avg_sim >= 0.28:
                    status = "Terjawab"
                    skor = int(min(98, max(75, round(avg_sim * 60 + 50))))
                    terjawab_count += 1
                else:
                    status = "Terjawab Sebagian"
                    skor = int(min(74, max(40, round(avg_sim * 50 + 30))))
                    terjawab_count += 1
                ringkasan = _summarize_answer_indonesian(questions[k], raw_text)

            pertanyaan_results.append({
                "nomor": k + 1,
                "pertanyaan": questions[k],
                "status": status,
                "skor_relevansi": skor,
                "waktu_mulai": t_start,
                "waktu_selesai": t_end,
                "ringkasan": ringkasan,
                "kutipan": raw_text
            })

        status_jawaban_teks = f"{terjawab_count} dari {total_pertanyaan} Pertanyaan Terjawab"
        ringkasan_jawaban = _generate_executive_summary(pertanyaan_results, terjawab_count, total_pertanyaan)

        return {
            "status": "SUKSES",
            "wps": wps,
            "status_jawaban_teks": status_jawaban_teks,
            "ringkasan_jawaban": ringkasan_jawaban,
            "analisis_pertanyaan": pertanyaan_results,
            "pertanyaan_terjawab_count": terjawab_count,
            "total_pertanyaan": total_pertanyaan,
            "full_transcript": full_transcript
        }

    def analisa_video(self, video_path: str, pertanyaan_perusahaan: str = "", pertanyaan_list: list = None, progress_callback=None) -> dict:
        if progress_callback:
            progress_callback(10, "Memulai analisis visual video (pose, wajah, iris)...")

        video_result = self._process_video_frames(video_path, progress_callback=progress_callback)

        if progress_callback:
            progress_callback(62, "Menganalisis audio & suara rekaman...")

        try:
            clip = VideoFileClip(video_path)
            durasi_video = clip.duration
            clip.close()
        except:
            durasi_video = 1

        audio_result = self._process_audio(video_path, pertanyaan_perusahaan, durasi_video, pertanyaan_list=pertanyaan_list, progress_callback=progress_callback)

        if audio_result.get("status") == "INVALID":
            return audio_result

        frame_count = video_result["frame_count"]
        valid_face_frames = video_result["valid_face_frames"]
        if frame_count == 0:
            return {"status": "INVALID", "pesan": "Format video tidak dapat diproses."}

        # 1. Parameter Analisis Nyata
        f = frame_count if frame_count > 0 else 1
        e_persen = round(video_result["kontak_mata_fokus_counter"] / f * 100, 1)
        g_persen = round(video_result["gerakan_tangan_counter"] / f * 100, 1)
        p_persen = round(video_result["gerakan_tubuh_counter"] / f * 100, 1)
        h_persen = round(video_result["gerakan_kepala_counter"] / f * 100, 1)
        wps = audio_result["wps"]
        wps_score = min(100.0, max(20.0, round((wps / 2.5) * 100, 1))) if wps > 0 else 50.0

        # 2. Kalkulasi Nuansa 5 Dimensi Psikologis
        ability_score = min(98.0, max(45.0, round(0.55 * wps_score + 0.45 * min(100.0, g_persen * 1.5 + 40.0), 1)))
        
        transcript_len = len(audio_result.get("full_transcript", "").split())
        depth_score = min(95.0, max(50.0, 60.0 + min(35.0, transcript_len * 0.8)))
        intelligent_score = min(98.0, max(45.0, round(0.5 * wps_score + 0.5 * depth_score, 1)))
        
        personality_score = min(98.0, max(45.0, round(0.5 * min(100.0, e_persen + 30.0) + 0.5 * min(100.0, p_persen + 25.0), 1)))
        
        attitude_score = min(98.0, max(45.0, round(0.6 * min(100.0, e_persen + 35.0) + 0.4 * min(100.0, 100.0 - abs(h_persen - 50.0)), 1)))
        
        tempo_stability = 92.0 if (1.5 <= wps <= 3.2) else (70.0 if wps > 0 else 50.0)
        ei_score = min(98.0, max(40.0, round(0.5 * tempo_stability + 0.5 * min(100.0, h_persen + 35.0), 1)))

        skor_keseluruhan = round((ability_score + intelligent_score + personality_score + attitude_score + ei_score) / 5.0, 1)

        if skor_keseluruhan >= 85.0: kategori = "Sangat Baik"
        elif skor_keseluruhan >= 70.0: kategori = "Baik"
        elif skor_keseluruhan >= 55.0: kategori = "Cukup"
        else: kategori = "Kurang"

        menit = int(durasi_video // 60)
        detik = int(durasi_video % 60)
        durasi_formatted = f"{menit:02d}:{detik:02d}"

        return {
            "status": "SUKSES",
            "kategori_fit": kategori,
            "skor_keseluruhan": skor_keseluruhan,
            "dimensi_psikologis": {
                "Ability": f"{ability_score}%",
                "Intelligent": f"{intelligent_score}%",
                "Personality": f"{personality_score}%",
                "Attitude": f"{attitude_score}%",
                "Emotional Intelligent": f"{ei_score}%"
            },
            "parameter_analisis": {
                "gerakan_tangan": min(100.0, round(g_persen, 1)),
                "gerakan_badan": min(100.0, round(p_persen, 1)),
                "gerakan_kepala": min(100.0, round(h_persen, 1)),
                "kontak_mata": min(100.0, round(e_persen, 1)),
                "word_per_second": round(wps, 2),
                "word_per_second_percent": round(wps_score, 1)
            },
            "durasi_video_detik": round(durasi_video, 1),
            "durasi_formatted": durasi_formatted,
            "ringkasan_jawaban": audio_result["ringkasan_jawaban"],
            "durasi_teks": video_result["durasi_teks"],
            "kualitas_teks": video_result["kualitas_teks"],
            "status_jawaban_teks": audio_result["status_jawaban_teks"],
            "analisis_pertanyaan": audio_result.get("analisis_pertanyaan", []),
            "pertanyaan_terjawab_count": audio_result.get("pertanyaan_terjawab_count", 0),
            "total_pertanyaan": audio_result.get("total_pertanyaan", 0),
            "full_transcript": audio_result.get("full_transcript", "")
        }

video_ai_service = VideoAIService()
