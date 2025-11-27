----------------------------------------------------
-- CATEGORY
----------------------------------------------------
CREATE TABLE IF NOT EXISTS category(
  category_id SERIAL PRIMARY KEY,
  category_name TEXT NOT NULL,
  alex_category_id TEXT UNIQUE
);

----------------------------------------------------
-- INSTITUTION
----------------------------------------------------
CREATE TABLE IF NOT EXISTS institution(
  institution_id SERIAL PRIMARY KEY,
  institution_name TEXT NOT NULL,
  country_code TEXT,
  alex_institution_id TEXT UNIQUE
);

----------------------------------------------------
-- AUTHOR
----------------------------------------------------
CREATE TABLE IF NOT EXISTS author(
  author_id SERIAL PRIMARY KEY,
  author_name TEXT NOT NULL,
  alex_author_id TEXT UNIQUE,
  institution_id INTEGER,
  citation_total INTEGER,
  main_topic_1 TEXT,
  main_topic_2 TEXT,
  main_topic_3 TEXT,
  FOREIGN KEY (institution_id) REFERENCES institution(institution_id)
);

----------------------------------------------------
-- PAPER
----------------------------------------------------
CREATE TABLE IF NOT EXISTS paper(
  paper_id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  category_id INTEGER,
  institution_id INTEGER,
  citation INTEGER,
  open_access BOOLEAN,
  locations TEXT,
  announcement_date DATE,
  weekly_count INTEGER DEFAULT 0,
  submit TEXT,
  alex_paper_id TEXT UNIQUE,
  FOREIGN KEY (category_id) REFERENCES category(category_id),
  FOREIGN KEY (institution_id) REFERENCES institution(institution_id)
);

----------------------------------------------------
-- ABSTRACT
----------------------------------------------------
CREATE TABLE IF NOT EXISTS abstract(
  paper_id INTEGER PRIMARY KEY,
  context TEXT,
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

----------------------------------------------------
-- YEAR-CITATION
----------------------------------------------------
CREATE TABLE IF NOT EXISTS yearcitation(
  paper_id INTEGER PRIMARY KEY,
  recent_year1_count INTEGER,
  recent_year2_count INTEGER,
  recent_year3_count INTEGER,
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

----------------------------------------------------
-- GUEST
----------------------------------------------------
CREATE TABLE IF NOT EXISTS guest(
  guest_id SERIAL PRIMARY KEY,
  guestname TEXT NOT NULL UNIQUE,
  pwd TEXT NOT NULL,
  interest_1 TEXT,
  interest_2 TEXT,
  interest_3 TEXT
);

----------------------------------------------------
-- GUEST FAVORITE
----------------------------------------------------
CREATE TABLE IF NOT EXISTS guestfavorite(
  favorite_id SERIAL PRIMARY KEY,
  guest_id INTEGER NOT NULL,
  paper_id INTEGER NOT NULL,
  UNIQUE(guest_id, paper_id),
  FOREIGN KEY (guest_id) REFERENCES guest(guest_id),
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

----------------------------------------------------
-- GUEST CATEGORY COUNT
----------------------------------------------------
CREATE TABLE IF NOT EXISTS guestcategorycount(
  ucc_id SERIAL PRIMARY KEY,
  guest_id INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  count INTEGER DEFAULT 0,
  FOREIGN KEY (guest_id) REFERENCES guest(guest_id),
  FOREIGN KEY (category_id) REFERENCES category(category_id)
);

----------------------------------------------------
-- AUTHOR–PAPER RELATION
----------------------------------------------------
CREATE TABLE IF NOT EXISTS authorpaper(
  ap_id SERIAL PRIMARY KEY,
  paper_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  UNIQUE(paper_id, author_id),
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id),
  FOREIGN KEY (author_id) REFERENCES author(author_id)
);
