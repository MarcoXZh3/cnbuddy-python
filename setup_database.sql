# Create user and password through root
mysql -u root -p
    CREATE USER IF NOT EXISTS 'cnbuddy'@'localhost' IDENTIFIED BY #'';    add password here
    CREATE DATABASE IF NOT EXISTS `cnbuddydb`;
    GRANT ALL ON cnbuddydb.* TO 'cnbuddy'@'localhost' IDENTIFIED BY #'';  add password here
    quit;


# Login to the user and setup
mysql -u cnbuddy -p
    USE cnbuddydb;

    DROP TABLE IF EXISTS `upvote_reply`;
    CREATE TABLE `upvote_reply` (
      `id`            int(11) NOT NULL AUTO_INCREMENT,
      `root_url`      text NOT NULL,
      `parent_author` text NOT NULL,
      `parent_link`   text NOT NULL,
      `body`          text,
      `reply_time`    datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `parent_link` (`parent_link`(1024))
    ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
    SHOW COLUMNS FROM `upvote_upvote`;

    DROP TABLE IF EXISTS `upvote_upvote`;
    CREATE TABLE `upvote_upvote` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `author`      text NOT NULL,
      `post_url`    text NOT NULL,
      `post_time`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      `vote_sp`     double NOT NULL,
      `vote_weight` double NOT NULL,
      `vote_power`  double NOT NULL,
      `vote_time`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `post_url` (`post_url`(1024))
    ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
