CREATE TABLE IF NOT EXISTS word_index (
  book_name TEXT NOT NULL,
  chapter_number INTEGER NOT NULL,
  verse_number INTEGER NOT NULL,
  token_index INTEGER NOT NULL,
  surface TEXT NOT NULL,
  strongs TEXT,
  lemma TEXT,
  morph TEXT,
  lang TEXT,
  PRIMARY KEY (book_name, chapter_number, verse_number, token_index)
);
