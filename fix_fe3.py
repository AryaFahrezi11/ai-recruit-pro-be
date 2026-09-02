import os

file_path = r"C:\ai-recruit-pro-FE\components\pipeline\CandidateModal.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

original_text = """                    <div className="space-y-4">
                      <div className="p-4 bg-muted/30 rounded-lg border border-border space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">{t.modal.durasiVideo}:</span>
                          <span className="font-semibold text-foreground">{t.modal.durasiDemo}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Status:</span>
                          <span className="font-semibold text-emerald-600 dark:text-emerald-400">{t.modal.pertanyaanSelesai}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Quality:</span>
                          <span className="font-semibold text-foreground">{t.modal.kualitasMedia}</span>
                        </div>
                      </div>

                      <div className="p-4 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900 rounded-lg">
                        <p className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-1">
                          {t.modal.transcriptHighlight}
                        </p>
                        <p className="text-xs italic text-foreground/80 leading-relaxed">
                          {t.modal.transkripCuplikan}
                        </p>
                      </div>
                    </div>"""

new_text = """                    <div className="space-y-4">
                      <div className="p-4 bg-muted/30 rounded-lg border border-border space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">{t.modal.durasiVideo}:</span>
                          <span className="font-semibold text-foreground">{candidate.aiResult?.durasi_teks || "Tersedia setelah analisis"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Status:</span>
                          <span className="font-semibold text-emerald-600 dark:text-emerald-400">{candidate.aiResult?.status_jawaban_teks || "Menunggu Analisis AI"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Quality:</span>
                          <span className="font-semibold text-foreground">{candidate.aiResult?.kualitas_teks || "Tersedia setelah analisis"}</span>
                        </div>
                      </div>

                      <div className="p-4 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900 rounded-lg">
                        <p className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-1">
                          {t.modal.transcriptHighlight}
                        </p>
                        <p className="text-xs italic text-foreground/80 leading-relaxed">
                          {candidate.aiResult?.ringkasan_jawaban || "Transkrip masih diproses oleh AI..."}
                        </p>
                      </div>
                    </div>"""

content = content.replace(original_text, new_text)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Modification complete.")
