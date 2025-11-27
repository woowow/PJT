CREATE TABLE guest (
  guest_id SERIAL PRIMARY KEY,
  guestname TEXT NOT NULL,
  pwd TEXT NOT NULL,
  interest_1 TEXT,
  interest_2 TEXT,
  interest_3 TEXT
);

CREATE TABLE category(
  category_id SERIAL PRIMARY KEY,
  category_name TEXT NOT NULL,
  alex_category_id TEXT UNIQUE
);

CREATE TABLE institution(
  institution_id SERIAL PRIMARY KEY,
  institution_name TEXT NOT NULL,
  country_code TEXT
);

CREATE TABLE author(
  author_id SERIAL PRIMARY KEY,
  author_name TEXT NOT NULL UNIQUE,
  institution_id INTEGER,
  citation_total INTEGER,
  main_topic_1 TEXT,
  main_topic_2 TEXT,
  main_topic_3 TEXT,
  alex_author_id TEXT UNIQUE,
  FOREIGN KEY (institution_id) REFERENCES institution(institution_id)
);

CREATE TABLE paper(
  paper_id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  category_id INTEGER NOT NULL,
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

CREATE TABLE abstract(
  paper_id INTEGER PRIMARY KEY,
  context TEXT,
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

CREATE TABLE yearcitation(
  paper_id INTEGER PRIMARY KEY,
  recent_year1_count INTEGER,
  recent_year2_count INTEGER,
  recent_year3_count INTEGER,
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

CREATE TABLE guestfavorite(
  favorite_id SERIAL PRIMARY KEY,
  guest_id INTEGER NOT NULL,
  paper_id INTEGER NOT NULL,
  UNIQUE(guest_id, paper_id),
  FOREIGN KEY (guest_id) REFERENCES guest(guest_id),
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

CREATE TABLE guestcategorycount(
  ucc_id SERIAL PRIMARY KEY,
  guest_id INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  count INTEGER DEFAULT 0,
  FOREIGN KEY (guest_id) REFERENCES guest(guest_id),
  FOREIGN KEY (category_id) REFERENCES category(category_id)
);

CREATE TABLE authorpaper(
  ap_id SERIAL PRIMARY KEY,
  paper_id INTEGER NOT NULL,
  author_id INTEGER NOT NULL,
  FOREIGN KEY (paper_id) REFERENCES paper(paper_id),
  FOREIGN KEY (author_id) REFERENCES author(author_id)
);
