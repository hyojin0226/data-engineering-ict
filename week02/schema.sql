CREATE DATABASE IF NOT EXISTS shop
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE shop;

CREATE TABLE IF NOT EXISTS quotes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    author VARCHAR(255) NOT NULL,
    quote_text VARCHAR(500) NOT NULL,
    tags TEXT NOT NULL,
    crawled_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_quotes_author_quote_text (author, quote_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;