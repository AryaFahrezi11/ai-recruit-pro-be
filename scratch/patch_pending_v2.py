file_path = 'c:/ai-recruit-pro-FE/app/pending-approval/page.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Patch header logo
old_header = """        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex flex-col">
            <span className="font-bold text-2xl tracking-tight text-slate-900 dark:text-white leading-none">
              AI-RecruitPro
            </span>
            <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mt-1">
              Portal Perusahaan
            </span>
          </div>
        </Link>"""

new_header = """        <Link href="/" className="flex items-center gap-3 group">
          <Image
            src="/logo_hd.png"
            alt="AI-RecruitPro Logo"
            width={280}
            height={280}
            quality={100}
            unoptimized
            className="h-10 sm:h-12 w-auto object-contain shrink-0 transition-transform group-hover:scale-105"
            priority
          />
          <div className="flex flex-col">
            <span className="font-extrabold text-xl tracking-tight text-slate-900 dark:text-white leading-none">
              AI-RecruitPro
            </span>
            <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mt-1">
              Portal Perusahaan
            </span>
          </div>
        </Link>"""

# 2. Patch natural wording
old_heading = """            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white leading-tight">
              {isRejected
                ? 'Pengajuan Verifikasi Akun Belum Disetujui'
                : 'Pendaftaran Berhasil Dikirim & Dalam Peninjauan Admin'}
            </h1>

            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed pt-2">
              {isRejected
                ? 'Admin telah meninjau pengajuan akun perusahaan Anda. Terdapat berkas legalitas atau data profil yang belum memenuhi kualifikasi. Silakan periksa catatan perbaikan dari admin di bawah ini.'
                : 'Terima kasih telah melengkapi data legalitas perusahaan & perwakilan HRD. Tim Administrator AI-Recruit Pro saat ini sedang memverifikasi keabsahan Dokumen NIB/NPWP dan ID Card Perusahaan Anda demi menjaga keamanan & kualitas ekosistem rekrutmen.'}
            </p>"""

new_heading = """            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white leading-tight">
              {isRejected
                ? 'Pengajuan Akun Perusahaan Memerlukan Perbaikan'
                : 'Pendaftaran Akun Berhasil Dikirim'}
            </h1>

            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed pt-1">
              {isRejected
                ? 'Tim kami telah memeriksa data perusahaan Anda dan menemukan beberapa berkas yang perlu diperbaiki. Silakan cek catatan admin di bawah ini.'
                : 'Terima kasih telah mendaftarkan perusahaan Anda. Tim admin kami sedang memeriksa berkas NIB/NPWP dan ID Card HRD yang telah Anda unggah. Kami akan mengabari Anda setelah proses verifikasi selesai.'}
            </p>"""

if old_header in content:
    content = content.replace(old_header, new_header)
    print("Header logo added successfully")
else:
    print("old_header not found")

if old_heading in content:
    content = content.replace(old_heading, new_heading)
    print("Heading copy naturalized successfully")
else:
    print("old_heading not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch v2 complete!")
