file_path = 'c:/ai-recruit-pro-FE/app/admin/reviews/page.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_use_effect = """  useEffect(() => {
    const qRating = searchParams.get('rating') || '';
    const qSearch = searchParams.get('search') || '';

    setFilterRating(qRating);
    setSearchInput(qSearch);
    setActiveSearch(qSearch);
    setCurrentPage(1);
    loadReviews(qSearch, qRating);
  }, [searchParams]);"""

new_use_effect = """  // Debounce auto-search via GET query parameters
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== activeSearch) {
        updateUrlParams({ search: searchInput });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    const qRating = searchParams.get('rating') || '';
    const qSearch = searchParams.get('search') || '';

    setFilterRating(qRating);
    setSearchInput(qSearch);
    setActiveSearch(qSearch);
    setCurrentPage(1);
    loadReviews(qSearch, qRating);
  }, [searchParams]);"""

if old_use_effect in content and 'Debounce auto-search' not in content:
    content = content.replace(old_use_effect, new_use_effect)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Debounced GET auto-search added successfully")
else:
    print("old_use_effect not found or already added")

print("Debounced search patch complete!")
