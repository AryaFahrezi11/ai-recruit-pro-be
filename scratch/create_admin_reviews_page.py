import os

target_dir = 'c:/ai-recruit-pro-FE/app/admin/reviews'
os.makedirs(target_dir, exist_ok=True)
target_file = os.path.join(target_dir, 'page.tsx')

page_content = """'use client';

import React, { useEffect, useState, useMemo, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Search,
  Star,
  Trash2,
  Filter,
  Eye,
  RefreshCw,
  MessageSquareQuote,
  CheckCircle2,
  X,
  AlertCircle,
  User,
  Building2,
  Calendar,
  Sparkles,
  ChevronDown
} from 'lucide-react';
import { fetchAuth } from '@/lib/api/auth';
import { toast } from 'react-hot-toast';
import { DataTable, ColumnDef } from '@/components/ui/DataTable';

interface ReviewItem {
  id: string;
  user_id?: string;
  name: string;
  role: string;
  rating: number;
  category?: string;
  comment?: string;
  is_anonymous: boolean;
  context_event?: string;
  created_at: string;
}

function AdminReviewsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialSearch = searchParams.get('search') || '';
  const initialRating = searchParams.get('rating') || '';

  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterRating, setFilterRating] = useState(initialRating);
  const [searchInput, setSearchInput] = useState(initialSearch);
  const [activeSearch, setActiveSearch] = useState(initialSearch);
  const [currentPage, setCurrentPage] = useState(1);

  // Modal States
  const [selectedReviewDetail, setSelectedReviewDetail] = useState<ReviewItem | null>(null);
  const [reviewToDelete, setReviewToDelete] = useState<ReviewItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const updateUrlParams = (updates: Record<string, string>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => {
      if (value && value !== '') {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });
    router.push(`?${params.toString()}`, { scroll: false });
  };

  const loadReviews = async (searchQuery: string = activeSearch, ratingQuery: string = filterRating) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (ratingQuery) params.append('rating', ratingQuery);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const url = params.toString() ? `/api/admin/reviews?${params.toString()}` : '/api/admin/reviews';
      const res = await fetchAuth(url, { method: 'GET' });
      const data = await res.json();
      setReviews(Array.isArray(data) ? data : []);
    } catch (error) {
      setReviews([]);
      toast.error('Gagal memuat data ulasan');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const qRating = searchParams.get('rating') || '';
    const qSearch = searchParams.get('search') || '';

    setFilterRating(qRating);
    setSearchInput(qSearch);
    setActiveSearch(qSearch);
    setCurrentPage(1);
    loadReviews(qSearch, qRating);
  }, [searchParams]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateUrlParams({ search: searchInput });
  };

  const handleClearSearch = () => {
    setSearchInput('');
    updateUrlParams({ search: '' });
  };

  const handleDeleteReview = async () => {
    if (!reviewToDelete) return;
    setIsDeleting(true);
    try {
      await fetchAuth(`/api/admin/reviews/${reviewToDelete.id}`, { method: 'DELETE' });
      toast.success('Ulasan berhasil dihapus');
      setReviewToDelete(null);
      loadReviews();
    } catch (error) {
      toast.error('Gagal menghapus ulasan');
    } finally {
      setIsDeleting(false);
    }
  };

  // Stats calculation
  const stats = useMemo(() => {
    const total = reviews.length;
    if (total === 0) return { total: 0, avgRating: 0, fiveStarCount: 0 };
    const sum = reviews.reduce((acc, r) => acc + (r.rating || 5), 0);
    const avgRating = (sum / total).toFixed(1);
    const fiveStarCount = reviews.filter(r => r.rating === 5).length;
    return { total, avgRating, fiveStarCount };
  }, [reviews]);

  // Table Columns
  const tableColumns: ColumnDef<ReviewItem>[] = [
    {
      key: 'no',
      header: 'No',
      align: 'center',
      className: 'w-12 text-center text-slate-500 dark:text-slate-400 font-semibold',
      headerClassName: 'w-12 text-center',
      render: (_, index) => index + 1
    },
    {
      key: 'pengulas',
      header: 'Pengulas & Peran',
      align: 'left',
      render: (r) => (
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-900 dark:text-white text-xs truncate">
              {r.name || 'Pengguna'}
            </span>
            {r.is_anonymous && (
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
                Anonim
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
            {r.role || 'Pelamar Kerja'}
          </span>
        </div>
      )
    },
    {
      key: 'rating',
      header: 'Penilaian',
      align: 'center',
      render: (r) => (
        <div className="flex items-center justify-center gap-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              size={13}
              className={i < (r.rating || 5) ? 'fill-amber-400 text-amber-400' : 'text-slate-200 dark:text-slate-700'}
            />
          ))}
          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 ml-1">
            {r.rating || 5}.0
          </span>
        </div>
      )
    },
    {
      key: 'category',
      header: 'Kategori',
      align: 'left',
      render: (r) => (
        <span className="inline-block px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          {r.category || 'Umum'}
        </span>
      )
    },
    {
      key: 'comment',
      header: 'Isi Ulasan / Feedback',
      align: 'left',
      render: (r) => (
        <div className="max-w-xs sm:max-w-sm truncate text-xs text-slate-700 dark:text-slate-300">
          {r.comment ? (
            <span>{r.comment}</span>
          ) : (
            <span className="italic text-slate-400">Tidak ada komentar tertulis</span>
          )}
        </div>
      )
    },
    {
      key: 'created_at',
      header: 'Tanggal Kirim',
      align: 'left',
      render: (r) => (
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          {r.created_at ? new Date(r.created_at).toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
          }) : '-'}
        </span>
      )
    },
    {
      key: 'actions',
      header: 'Aksi',
      align: 'center',
      render: (r) => (
        <div className="flex items-center justify-center gap-1.5">
          <button
            onClick={() => setSelectedReviewDetail(r)}
            title="Lihat Detail Ulasan"
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <Eye size={15} />
          </button>
          <button
            onClick={() => setReviewToDelete(r)}
            title="Hapus Ulasan"
            className="p-1.5 rounded-lg text-rose-500 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
          >
            <Trash2 size={15} />
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
            <MessageSquareQuote className="text-slate-900 dark:text-white" size={24} />
            Manajemen Ulasan & Feedback
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Kelola ulasan, masukan pengguna, dan penilaian bintang yang dikirimkan oleh pelamar & perusahaan.
          </p>
        </div>

        <button
          onClick={() => loadReviews()}
          disabled={isLoading}
          className="self-start sm:self-auto px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/60 font-bold text-xs flex items-center gap-2 transition-all shadow-2xs"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Muat Ulang Data</span>
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-[#1A4B9F] dark:text-blue-400 flex items-center justify-center shrink-0">
            <MessageSquareQuote size={22} />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Total Ulasan</span>
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5 block">{stats.total}</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-500 flex items-center justify-center shrink-0">
            <Star size={22} className="fill-amber-400" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Rata-Rata Penilaian</span>
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5 block">{stats.avgRating} / 5.0</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Bintang 5 Sempurna</span>
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5 block">{stats.fiveStarCount}</span>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Cari nama pengulas, isi komentar..."
            className="w-full pl-9 pr-8 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-xs font-medium text-slate-900 dark:text-white focus:outline-none focus:border-slate-400"
          />
          {searchInput && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X size={14} />
            </button>
          )}
        </form>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <div className="relative">
            <select
              value={filterRating}
              onChange={(e) => updateUrlParams({ rating: e.target.value })}
              className="appearance-none bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl px-3.5 py-2 pr-8 text-xs font-semibold text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="">Semua Penilaian (Star)</option>
              <option value="5">5 Bintang (Sempurna)</option>
              <option value="4">4 Bintang (Sangat Baik)</option>
              <option value="3">3 Bintang (Cukup)</option>
              <option value="2">2 Bintang (Kurang)</option>
              <option value="1">1 Bintang (Buruk)</option>
            </select>
            <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>

          {(activeSearch || filterRating) && (
            <button
              onClick={() => updateUrlParams({ search: '', rating: '' })}
              className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 text-xs font-bold transition-colors"
            >
              Reset Filter
            </button>
          )}
        </div>
      </div>

      {/* Main DataTable */}
      <DataTable
        columns={tableColumns}
        data={reviews}
        isLoading={isLoading}
        currentPage={currentPage}
        pageSize={10}
        onPageChange={(page) => setCurrentPage(page)}
      />

      {/* Detail Modal */}
      {selectedReviewDetail && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 w-full max-w-lg rounded-2xl shadow-xl p-6 space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <MessageSquareQuote size={18} />
                Detail Ulasan Pengguna
              </h3>
              <button
                onClick={() => setSelectedReviewDetail(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-900 dark:text-white block">
                    {selectedReviewDetail.name || 'Pengguna'}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    {selectedReviewDetail.role || 'Pelamar Kerja'}
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      size={14}
                      className={i < (selectedReviewDetail.rating || 5) ? 'fill-amber-400 text-amber-400' : 'text-slate-200 dark:text-slate-700'}
                    />
                  ))}
                </div>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/60 text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                {selectedReviewDetail.comment || 'Tidak ada komentar tertulis.'}
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 block uppercase">Kategori</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedReviewDetail.category || 'Umum'}</span>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/30 rounded-xl border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 block uppercase">Waktu Kirim</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {selectedReviewDetail.created_at ? new Date(selectedReviewDetail.created_at).toLocaleString('id-ID') : '-'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedReviewDetail(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-bold text-xs hover:bg-slate-200 transition-colors"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {reviewToDelete && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 w-full max-w-sm rounded-2xl shadow-xl p-6 space-y-4 animate-in fade-in zoom-in-95">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Konfirmasi Hapus Ulasan</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Apakah Anda yakin ingin menghapus ulasan dari <strong>{reviewToDelete.name}</strong> secara permanen?
            </p>
            <div className="flex justify-end gap-2.5 pt-2">
              <button
                onClick={() => setReviewToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Batal
              </button>
              <button
                onClick={handleDeleteReview}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white transition-colors flex items-center gap-1.5"
              >
                {isDeleting ? 'Menghapus...' : 'Ya, Hapus Ulasan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AdminReviewsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-medium text-slate-400">Memuat manajemen ulasan...</div>}>
      <AdminReviewsContent />
    </Suspense>
  );
}
"""

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(page_content)

print(f"Created admin reviews page at {target_file}")
