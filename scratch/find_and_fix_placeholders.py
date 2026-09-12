import os

fe_dir = 'c:/ai-recruit-pro-FE'

files_to_check = [
    'app/(perusahaan)/jobs/new/page.tsx',
    'app/applicant/upload-cv/page.tsx',
    'lib/i18n/dictionaries.ts'
]

for rel_path in files_to_check:
    full_path = os.path.join(fe_dir, rel_path)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        continue

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    if rel_path == 'app/(perusahaan)/jobs/new/page.tsx':
        content = content.replace(
            'placeholder="Misal: Merancang arsitektur frontend web aplikasi berskala besar"',
            'placeholder="Misal: Mengelola operasional harian dan koordinasi tim kerja"'
        )
        content = content.replace(
            'placeholder="Contoh: Blockchain, AI Engineering, Legal & Compliance..."',
            'placeholder="Contoh: Manajemen Proyek, Komunikasi Bisnis, Legal & Compliance..."'
        )

    elif rel_path == 'app/applicant/upload-cv/page.tsx':
        content = content.replace(
            'placeholder="Frontend Engineer / Staff Marketing"',
            'placeholder="Manajer Operasional / Staff Marketing"'
        )
        content = content.replace(
            'placeholder="Senior Frontend Engineer"',
            'placeholder="Spesialis Komunikasi / Manajer Proyek"'
        )

    elif rel_path == 'lib/i18n/dictionaries.ts':
        content = content.replace(
            "jobTitlePlaceholder: 'misal: Senior Frontend Engineer'",
            "jobTitlePlaceholder: 'misal: Manajer Pemasaran / Manajer Proyek'"
        )
        content = content.replace(
            "aiKeywordsPlaceholder: 'Masukkan keahlian inti seperti: React, TypeScript (tekan Enter)'",
            "aiKeywordsPlaceholder: 'Masukkan keahlian inti seperti: Manajemen Proyek, Analisis Data (tekan Enter)'"
        )
        content = content.replace(
            "skillsPlaceholder: 'misal: React, Node.js, Manajemen Proyek'",
            "skillsPlaceholder: 'misal: Manajemen Proyek, Komunikasi Bisnis, Analisis Data'"
        )
        content = content.replace(
            "jobTitlePlaceholder: 'e.g., Senior Frontend Engineer'",
            "jobTitlePlaceholder: 'e.g., Marketing Manager / Project Manager'"
        )
        content = content.replace(
            "aiKeywordsPlaceholder: 'Input core skills like: React, TypeScript (press Enter)'",
            "aiKeywordsPlaceholder: 'Input core skills like: Project Management, Data Analysis (press Enter)'"
        )
        content = content.replace(
            "skillsPlaceholder: 'e.g. React, Node.js, Project Management'",
            "skillsPlaceholder: 'e.g. Project Management, Business Communication, Data Analysis'"
        )
        content = content.replace(
            "pengalamanDemo: '3.5 Tahun Pengembang Frontend Senior'",
            "pengalamanDemo: '3.5 Tahun Manajer Operasional & Tim'"
        )

    if content != original:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated placeholders in {rel_path}")
    else:
        print(f"No changes made to {rel_path}")

print("Placeholder updates completed successfully!")
