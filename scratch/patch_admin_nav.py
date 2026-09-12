path = 'c:/ai-recruit-pro-FE/app/admin/layout.tsx'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add MessageSquareQuote to lucide-react import
if 'MessageSquareQuote' not in content:
    content = content.replace(
        '  LayoutDashboard, Users, ShieldCheck, LogOut, Settings, Bell, Search, Menu, X, Briefcase, Database, LineChart, FileText',
        '  LayoutDashboard, Users, ShieldCheck, LogOut, Settings, Bell, Search, Menu, X, Briefcase, Database, LineChart, FileText, MessageSquareQuote'
    )

# Add Ulasan & Feedback to navItems
old_nav = """    { label: 'Verifikasi Perusahaan', icon: ShieldCheck, href: '/admin/verifikasi' },
    { label: 'Master Data', icon: Database, href: '/admin/master-data' },"""

new_nav = """    { label: 'Verifikasi Perusahaan', icon: ShieldCheck, href: '/admin/verifikasi' },
    { label: 'Ulasan & Feedback', icon: MessageSquareQuote, href: '/admin/reviews' },
    { label: 'Master Data', icon: Database, href: '/admin/master-data' },"""

if old_nav in content:
    content = content.replace(old_nav, new_nav)
    print("Added Ulasan & Feedback to navItems")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Admin nav patch complete!")
