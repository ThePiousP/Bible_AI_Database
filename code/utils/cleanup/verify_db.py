import sqlite3

conn = sqlite3.connect('GoodBook.db')
cur = conn.cursor()

# Count records
cur.execute('SELECT COUNT(*) FROM verses')
print(f'Total verses: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM books')
print(f'Total books: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM chapters')
print(f'Total chapters: {cur.fetchone()[0]}')

# Sample verses
cur.execute('SELECT book_name, text_plain FROM verses v JOIN books b ON v.book_id = b.id WHERE chapter_id = 1 AND verse_number = 1 LIMIT 3')
print('\nFirst verses:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1][:60]}...')

conn.close()
