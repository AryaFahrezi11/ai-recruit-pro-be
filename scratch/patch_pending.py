file_path = 'c:/ai-recruit-pro-FE/app/pending-approval/page.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_icon_block = """          {/* Animated Status Icon */}
          {isRejected ? (
            <div className="w-20 h-20 bg-rose-50 dark:bg-rose-950/40 border-2 border-rose-200 dark:border-rose-800/60 rounded-3xl flex items-center justify-center text-rose-600 dark:text-rose-400 mx-auto shadow-sm relative">
              <XCircle size={40} />
            </div>
          ) : (
            <div className="w-20 h-20 bg-blue-50 dark:bg-blue-950/40 border-2 border-blue-200 dark:border-blue-800/60 rounded-3xl flex items-center justify-center text-[#1A4B9F] dark:text-blue-400 mx-auto shadow-sm relative">
              <Clock size={36} className="animate-spin" style={{ animationDuration: '8s' }} />
              <div className="absolute -top-1 -right-1 w-6 h-6 bg-amber-500 text-white rounded-full flex items-center justify-center font-black text-[10px] shadow-sm">
                !
              </div>
            </div>
          )}"""

new_icon_block = """          {/* Animated Status Icon */}
          {isRejected && (
            <div className="w-20 h-20 bg-rose-50 dark:bg-rose-950/40 border-2 border-rose-200 dark:border-rose-800/60 rounded-3xl flex items-center justify-center text-rose-600 dark:text-rose-400 mx-auto shadow-sm relative">
              <XCircle size={40} />
            </div>
          )}"""

old_badge_block = """          {/* Heading & Notice */}
          <div className="space-y-3 max-w-xl mx-auto">
            {isRejected ? (
              <span className="inline-block px-4 py-1.5 rounded-full bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-400 font-extrabold text-xs border border-rose-200 dark:border-rose-800 uppercase tracking-wider">
                Verifikasi Ditolak / Perlu Perbaikan
              </span>
            ) : (
              <span className="inline-block px-4 py-1.5 rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 font-extrabold text-xs border border-amber-200 dark:border-amber-800 uppercase tracking-wider">
                Verifikasi Dalam Proses
              </span>
            )}"""

new_badge_block = """          {/* Heading & Notice */}
          <div className="space-y-3 max-w-xl mx-auto">
            {isRejected && (
              <span className="inline-block px-4 py-1.5 rounded-full bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-400 font-extrabold text-xs border border-rose-200 dark:border-rose-800 uppercase tracking-wider">
                Verifikasi Ditolak / Perlu Perbaikan
              </span>
            )}"""

if old_icon_block in content:
    content = content.replace(old_icon_block, new_icon_block)
    print("Replaced clock icon block successfully")
else:
    print("old_icon_block not found")

if old_badge_block in content:
    content = content.replace(old_badge_block, new_badge_block)
    print("Replaced badge block successfully")
else:
    print("old_badge_block not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Pending approval page update complete!")
