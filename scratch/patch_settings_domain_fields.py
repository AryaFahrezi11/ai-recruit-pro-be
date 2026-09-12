file_path = 'c:/ai-recruit-pro-FE/app/admin/settings/page.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initial state defaults
old_state = """  const [settings, setSettings] = useState<Record<string, any>>({
    maintenance_mode: false,
    seo_title: '',
    seo_description: '',"""

new_state = """  const [settings, setSettings] = useState<Record<string, any>>({
    maintenance_mode: false,
    seo_title: '',
    seo_description: '',
    public_domain_url: '',
    public_backend_url: '',
    support_whatsapp: '',
    lokasi_kantor_pusat: '',"""

if old_state in content:
    content = content.replace(old_state, new_state)

# 2. Update General Settings JSX
old_general_jsx = """          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-extrabold text-slate-900 dark:text-white mb-4">Pengaturan Umum & SEO</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Judul Aplikasi (SEO Title)</label>
                    <input 
                      type="text" 
                      value={settings.seo_title || ''}
                      onChange={(e) => handleChange('seo_title', e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Deskripsi Meta (SEO Description)</label>
                    <textarea 
                      value={settings.seo_description || ''}
                      onChange={(e) => handleChange('seo_description', e.target.value)}
                      rows={3}
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none resize-none font-medium"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}"""

new_general_jsx = """          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-extrabold text-slate-900 dark:text-white mb-4">Pengaturan Umum, SEO & Domain Resmi</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Domain Resmi Utama Website (Frontend Public Domain)</label>
                    <input 
                      type="text" 
                      value={settings.public_domain_url || ''}
                      onChange={(e) => handleChange('public_domain_url', e.target.value)}
                      placeholder="https://airecruitpro.com"
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none font-medium"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">Alamat domain resmi website utama yang diakses oleh publik (misal: https://airecruitpro.com).</p>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">URL Server Backend API Resmi (Backend Public Domain)</label>
                    <input 
                      type="text" 
                      value={settings.public_backend_url || ''}
                      onChange={(e) => handleChange('public_backend_url', e.target.value)}
                      placeholder="https://api.airecruitpro.com"
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none font-medium"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">Alamat URL server backend API resmi untuk pengiriman email notifikasi, reset password & media.</p>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Judul Aplikasi (SEO Title)</label>
                    <input 
                      type="text" 
                      value={settings.seo_title || ''}
                      onChange={(e) => handleChange('seo_title', e.target.value)}
                      placeholder="AI Recruit Pro - Platform Rekrutmen & Lowongan Kerja Berbasis AI"
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Deskripsi Meta (SEO Description)</label>
                    <textarea 
                      value={settings.seo_description || ''}
                      onChange={(e) => handleChange('seo_description', e.target.value)}
                      rows={3}
                      placeholder="Temukan talenta terbaik dan lowongan kerja impian dengan analisis CV otomatis, screening video, dan proses transparan di AI Recruit Pro."
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none resize-none font-medium"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Nomor WhatsApp Support / Helpdesk</label>
                      <input 
                        type="text" 
                        value={settings.support_whatsapp || ''}
                        onChange={(e) => handleChange('support_whatsapp', e.target.value)}
                        placeholder="+62 812-3456-7890"
                        className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Lokasi Kantor Pusat / Kota</label>
                      <input 
                        type="text" 
                        value={settings.lokasi_kantor_pusat || ''}
                        onChange={(e) => handleChange('lokasi_kantor_pusat', e.target.value)}
                        placeholder="Jakarta, Indonesia"
                        className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-slate-400 outline-none font-medium"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}"""

if old_general_jsx in content:
    content = content.replace(old_general_jsx, new_general_jsx)
    print("Updated General Tab JSX with Domain & SEO fields")
else:
    print("old_general_jsx not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Settings domain fields patch complete!")
