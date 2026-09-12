file_path = 'c:/ai-recruit-pro-FE/app/admin/reviews/page.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove debounced useEffect
debounce_block = """  // Debounce auto-search via GET query parameters
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== activeSearch) {
        updateUrlParams({ search: searchInput });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);\n\n"""

if debounce_block in content:
    content = content.replace(debounce_block, "")
    print("Removed debounced auto-search")
else:
    print("debounce_block not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Enter search patch complete!")
